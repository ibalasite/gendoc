```
PetPage (owner authenticated via Bearer token)
  ↓ clicks TrainingEntry
TrainingPage /pet/:petId/train
  │
  ├─ TrainingActions shows 3 action cards (RUN / STRENGTH / STAMINA)
  │    Each card shows current stat value and trains-remaining count
  │    training_actions_per_day = 3 actions per UTC day
  │
  ├─ User clicks "Train" on a card
  │    → POST /api/v1/pets/:petId/train  { trainingType: 'RUN' | 'STRENGTH' | 'STAMINA' }
  │    ← { updatedStats, statDelta, actionsRemainingToday }
  │
  ├─ On success:
  │    StatChangeIndicator appears: "+X Speed" floats up, visible for
  │    training_stat_display_duration_seconds = 2 seconds
  │    Stat bars animate to new values
  │    usePet cache is invalidated → PetPage re-fetches
  │
  ├─ Error states:
  │    HTTP 400 VALIDATION_ERROR → toast: "Invalid training type. Please try again."
  │    HTTP 400 TRAINING_LIMIT_REACHED → all action cards disabled; DailyResetTimer shown
  │    HTTP 400 STAT_AT_MAXIMUM → toast: "Stat is already at maximum (pet_stat_max = 100)"; card remains
  │                                enabled for other stats not yet at max
  │    HTTP 401 → handled globally: clearPetToken() + redirect to /
  │    HTTP 403 NOT_OWNER → toast: "You do not own this pet." (should not occur in normal flow)
  │    HTTP 404 PET_NOT_FOUND → toast: "Pet not found. Please reload and try again." (should not occur in normal flow)
  │
  └─ Exhausted (actionsRemainingToday = 0):
       DailyResetTimer shows countdown to UTC 00:00 reset
       All action cards disabled

  Neglect check: if last_trained_at > training_neglect_threshold_days = 3 days ago
    → NeglectedState overlay renders on PetCanvas
```