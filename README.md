# llm_env

This repository contains a minimal Django project used for experiments with large language models.

## Inference page

Open `/inference/` to generate a new `InferenceResult`. The page now lets you enter the system prompt, a user prompt and any number of image URLs. Add more image URL fields with the **+** button. Submitting the form creates a record and redirects to its evaluation page.

## Evaluation page

Run the Django server and open `/evaluation/` to view a simple UI for rating the output of a language model.
