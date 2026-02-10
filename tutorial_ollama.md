## Steps to install and configure OLLAMA:

1. Download OLLAMA from [ollama](https://ollama.com/download/windows).
2. If we are running the model on our CPU alone, then we need to set a special env variable. This will mostly be the case when hosting on a simple small server
    - On Windows:
        1. Open a CMD prompt window.
        2. Run: `set CUDA_VISIBLE_DEVICES=` We want the env var to be empty.
        3. Then run: `ollama serve`.
    - On Linux:
        1. Open a bash session.
        2. Run: `CUDA_VISIBLE_DEVICES="" ollama serve`.

    This runs a server in the background which helps python communicate to the LLM models.
3. We need to download a good LLM Model, to act as the agent. Here is what I've observed. If we get access to a GPU server, we can install a better model, and it will run fast as well. Otherwise, we'll have to makedo with a smaller model. It still runs, but its not THAT fast.
4. Open another CMD session and run: `ollama pull gemma3:4b-it-qat` for the smaller model. For the larger model run: `ollama pull gemma3:12b-it-qat`. This will take a min to download. You can close this session later.
5. Update the `.env` file with the model name. (REMEMBER, `.env`, not `.env.example`).
6. Open another cmd window and type: `ollama run <model_name>`, this will start the model, and keep it loaded and running. Then type `/bye` in the prompt window it gives, to close the cmd session.
7. Now run the tests as usual.
        