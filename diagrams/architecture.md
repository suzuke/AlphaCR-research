```mermaid
flowchart LR
    A[Deterministic Simulator] --> B[Human Match Replay]
    B --> C[Imitation Learning]
    C --> D[Self-play RL / PPO]
    D --> E[Evaluation]
    E --> F[Online Play]
    A -.-> G[Counterfactual Verification - in progress]
```
