# llm_env

This repository contains a minimal Django project used for experiments with large language models.

## Inference page

Open `/inference/` to generate a new `InferenceResult`. The page provides a simple form for entering the system prompt, an optional user prompt and one or more image URLs. Submitting the form creates a record and redirects to the evaluation page for that result.

## Evaluation page

Run the Django server and open `/evaluation/` to view a simple UI for rating the output of a language model.
