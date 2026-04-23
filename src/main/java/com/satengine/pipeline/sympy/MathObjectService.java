package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.sympy.SymPyQuestionRepository;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/**
 * Wraps the math_engine.py subprocess.
 *
 * Key responsibilities:
 *  - Invoke Python with --skill / --difficulty / --count and optional exclusion flags
 *  - Parse each stdout line as a MathObject
 *  - Validate: non-null verifiedAnswer, 3 distractors for MCQ
 *  - Duplicate detection via param_hash (delegates to repo)
 *  - Answer-slot assignment: deterministic Fisher-Yates using SHA-256 of externalId
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MathObjectService {

    @Value("${sympy.python.interpreter:python3}")
    private String pythonInterpreter;

    @Value("${sympy.python.script:scripts/math_engine.py}")
    private String mathEngineScript;

    private final SymPyQuestionRepository sympyRepo;
    private final ObjectMapper objectMapper;

    @PostConstruct
    public void verifyPythonEnv() {
        try {
            ProcessBuilder pb = new ProcessBuilder(pythonInterpreter, "-c", "import sympy; print(sympy.__version__)");
            pb.redirectErrorStream(true);
            Process p = pb.start();
            String out = new String(p.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            int exit = p.waitFor();
            if (exit != 0) {
                log.warn("SymPy not importable via '{}' — sympy-generate job will fail. " +
                         "Set sympy.python.interpreter in application-local.yml", pythonInterpreter);
            } else {
                log.info("SymPy {} available at '{}'", out, pythonInterpreter);
            }
        } catch (Exception e) {
            log.warn("Could not verify Python env (interpreter='{}'): {}", pythonInterpreter, e.getMessage());
        }
    }

    /**
     * Generate {@code count} MathObjects for the given skill + difficulty.
     *
     * @param skill            skill key (e.g. "linear_eq_one_var") or null for round-robin all
     * @param difficulty       1–3 (SAT taxonomy: 1=Easy, 2=Medium, 3=Hard; clamped to 3 in Python)
     * @param count            number of questions
     * @param excludeParams    param hashes to skip (prevents duplicates across retries)
     * @param excludeScenarios scenario tags to avoid for word-problem skills
     * @return list of validated MathObjects
     */
    public List<MathObject> generate(String skill, int difficulty, int count,
                                     Set<String> excludeParams, Set<String> excludeScenarios) {
        return generate(skill, difficulty, count, excludeParams, excludeScenarios, null, Set.of());
    }

    /** Overload without variant/excludeTemplates — backward-compatible shorthand. */
    public List<MathObject> generate(String skill, int difficulty, int count,
                                     Set<String> excludeParams, Set<String> excludeScenarios,
                                     String forceTemplate) {
        return generate(skill, difficulty, count, excludeParams, excludeScenarios,
                        forceTemplate, null, Set.of());
    }

    /** Overload with excludeTemplates but without forceVariant. */
    public List<MathObject> generate(String skill, int difficulty, int count,
                                     Set<String> excludeParams, Set<String> excludeScenarios,
                                     String forceTemplate, Set<String> excludeTemplates) {
        return generate(skill, difficulty, count, excludeParams, excludeScenarios,
                        forceTemplate, null, excludeTemplates);
    }

    /**
     * Full generate with optional template + variant pin.
     *
     * @param forceTemplate    if non-null, passed as --template to math_engine.py
     * @param forceVariant     if non-null, passed as --variant to math_engine.py
     * @param excludeTemplates template names already used in this batch (may be empty)
     */
    public List<MathObject> generate(String skill, int difficulty, int count,
                                     Set<String> excludeParams, Set<String> excludeScenarios,
                                     String forceTemplate, String forceVariant,
                                     Set<String> excludeTemplates) {
        List<String> cmd = new ArrayList<>(Arrays.asList(
                pythonInterpreter, mathEngineScript,
                "--skill=" + (skill != null ? skill : "all"),
                "--difficulty=" + difficulty,
                "--count=" + count
        ));
        if (!excludeParams.isEmpty()) {
            cmd.add("--exclude-params=" + String.join(",", excludeParams));
        }
        if (!excludeScenarios.isEmpty()) {
            cmd.add("--exclude-scenarios=" + String.join(",", excludeScenarios));
        }
        if (excludeTemplates != null && !excludeTemplates.isEmpty()) {
            cmd.add("--exclude-templates=" + String.join(",", excludeTemplates));
        }
        if (forceTemplate != null && !forceTemplate.isBlank()) {
            cmd.add("--template=" + forceTemplate);
        }
        if (forceVariant != null && !forceVariant.isBlank()) {
            cmd.add("--variant=" + forceVariant);
        }

        log.debug("Running math_engine: {}", String.join(" ", cmd));

        try {
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(false);
            Process process = pb.start();

            List<MathObject> results = new ArrayList<>();
            try (BufferedReader stdout = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = stdout.readLine()) != null) {
                    line = line.strip();
                    if (line.isEmpty()) continue;
                    MathObject mo = objectMapper.readValue(line, MathObject.class);
                    if (mo.hasError()) {
                        throw new MathTemplateException("math_engine returned error: " + mo.error());
                    }
                    results.add(mo);
                }
            }

            // Drain stderr for logging
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            int exitCode = process.waitFor();

            if (exitCode != 0) {
                throw new MathTemplateException(
                        "math_engine.py exited with code " + exitCode +
                        (stderr.isBlank() ? "" : ": " + stderr.lines().findFirst().orElse(stderr)));
            }
            if (!stderr.isBlank()) {
                log.warn("math_engine stderr: {}", stderr);
            }

            return results;

        } catch (MathTemplateException e) {
            throw e;
        } catch (Exception e) {
            throw new MathTemplateException("Failed to invoke math_engine.py", e);
        }
    }

    /**
     * Query available variants for a given skill + difficulty (+ optional template).
     *
     * Invokes: math_engine.py --skill=X --difficulty=D --list-variants [--template=T]
     *
     * Returns raw JSON string from Python, e.g.:
     *   {"template_name": ["variant1", "variant2"], ...}
     * or for a specific template:
     *   {"variants": ["variant1", "variant2"]}
     */
    public String listVariants(String skill, int difficulty, String template) {
        List<String> cmd = new ArrayList<>(Arrays.asList(
                pythonInterpreter, mathEngineScript,
                "--skill=" + skill,
                "--difficulty=" + difficulty,
                "--list-variants"
        ));
        if (template != null && !template.isBlank()) {
            cmd.add("--template=" + template);
        }
        try {
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(false);
            Process process = pb.start();
            String stdout = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            String stderr = new String(process.getErrorStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new MathTemplateException(
                        "math_engine.py --list-variants exited with code " + exitCode +
                        (stderr.isBlank() ? "" : ": " + stderr));
            }
            return stdout;
        } catch (MathTemplateException e) {
            throw e;
        } catch (Exception e) {
            throw new MathTemplateException("Failed to invoke math_engine.py --list-variants", e);
        }
    }

    /**
     * Validate a MathObject before saving.
     * Throws {@link MathTemplateException} if anything is wrong.
     */
    public void validate(MathObject mo) {
        if (mo.verifiedAnswer() == null || mo.verifiedAnswer().isBlank()) {
            throw new MathTemplateException("MathObject missing verifiedAnswer: " + mo.skill());
        }
        if ("mcq".equals(mo.questionType())) {
            if (mo.distractors() == null || mo.distractors().size() < 3) {
                throw new MathTemplateException("MCQ requires 3 distractors, got: " + mo.distractors());
            }
        }
        if ("spr".equals(mo.questionType())) {
            if (mo.sprMin() == null || mo.sprMax() == null) {
                throw new MathTemplateException("SPR question missing sprMin/sprMax");
            }
        }
    }

    /**
     * True when a question with the same paramHash already exists for this skill.
     */
    public boolean isDuplicateParameters(String skillKey, String paramHash) {
        return sympyRepo.existsBySkillKeyAndParamHash(skillKey, paramHash);
    }

    /**
     * Deterministically shuffle [verifiedAnswer] + distractors into slots A-D.
     * Seed = first 8 bytes of SHA-256(externalId) as a long.
     *
     * Returns the correct answer letter ("A", "B", "C", or "D").
     * Populates optionA/B/C/D in the provided {@code slots} array (index 0-3).
     */
    public String assignAnswerSlot(MathObject mo, String externalId, String[] slots) {
        List<String> options = new ArrayList<>();
        options.add(mo.verifiedAnswer());
        options.addAll(mo.distractors());

        long seed = sha256Seed(externalId);
        Collections.shuffle(options, new Random(seed));

        String[] letters = {"A", "B", "C", "D"};
        String correctLetter = null;
        for (int i = 0; i < 4; i++) {
            slots[i] = options.get(i);
            if (options.get(i).equals(mo.verifiedAnswer())) {
                correctLetter = letters[i];
            }
        }
        return correctLetter;
    }

    private long sha256Seed(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(input.getBytes(StandardCharsets.UTF_8));
            long seed = 0;
            for (int i = 0; i < 8; i++) {
                seed = (seed << 8) | (hash[i] & 0xFF);
            }
            return seed;
        } catch (Exception e) {
            return input.hashCode();
        }
    }
}
