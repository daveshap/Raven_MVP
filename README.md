# Raven Minimum Viable Product

Minimum Viable Product for Raven using GPT-3. See https://ravenagi.io/ for more information.

## Usage

1. Create `openaiapikey.txt` in this directory with your API key as the first and only line. This file is excluded via `.gitignore` so you don't have to worry about accidentally sharing your key.
2. Install `openai` with `pip install openai`
3. Start `nexus.py`, the web interface is accessible via http://127.0.0.1:9999/nexus
4. Start use the **Microservices** page to start remaining services
5. Use the **Context** to inject a context into the nexus.

## MVP Services

These are the barebones services required to demonstrate Raven as a thinking machine. 

| Service | Description |
|---|---|
| Nexus | Stores the stream of consciousness, allows for arbitrary number of microservices to participate. |
| Action Generator | Ingests contexts and generates action ideas. |
| Core Objective Functions | Ingest context and action ideas, evaluates actions based on their merits. |
| Iterator | Ingests context, action ideas, and COF evaluations then generates new action ideas based upon feedback. |

## Roadmap Services

These are services on the roadmap

| Service | Description |
|---|---|
| Arbiter | Looks at all available actions and picks the best one based upon other criteria such as feasibility. |
| Executive | Looks for arbitration messages and acts upon the world. |
| Recall | Stores and retrieves messages from the nexus for long term memory. Uses keyword extraction from contexts to query recall database. |
| Encyclopedia | Uses keyword extraction from contexts to find interesting relevant information from external sources. |
| Inhibitor | Deletes contexts and related messages from the nexus once executive action has been taken. |
| Augmenter | Uses recall and encyclopedia messages to synthesize new and better contexts. |
| Context | Passively watches/listens to outside world to automatically generate contexts. |