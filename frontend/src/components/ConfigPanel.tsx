import type { GAConfig } from "../types";
import { DEFAULT_CONFIG } from "../types";

interface Props {
  config: GAConfig;
  onChange: (config: GAConfig) => void;
  disabled: boolean;
}

function Field({
  label,
  sublabel,
  value,
  onChange,
  step = 1,
  min,
  max,
  disabled,
}: {
  label: string;
  sublabel: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
  disabled: boolean;
}) {
  return (
    <div className="form-field">
      <div className="field-labels">
        <label>{label}</label>
        <span className="field-sublabel">{sublabel}</span>
      </div>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

export default function ConfigPanel({ config, onChange, disabled }: Props) {
  const set = (patch: Partial<GAConfig>) => onChange({ ...config, ...patch });

  return (
    <div className="card config-card">
      <div className="card-header-row">
        <h2>GA Hyperparameter Configuration</h2>
        <button
          type="button"
          className="reset-link-btn"
          disabled={disabled}
          onClick={() => onChange(DEFAULT_CONFIG)}
          title="Reset to default hyperparameters"
        >
          Reset Defaults
        </button>
      </div>

      <div className="grid cols-4 config-grid">
        <Field
          label="Population size"
          sublabel="Candidates per gen"
          value={config.population_size}
          min={10}
          max={1000}
          onChange={(v) => set({ population_size: v })}
          disabled={disabled}
        />
        <Field
          label="Max Generations"
          sublabel="Hard stopping cap"
          value={config.generations}
          min={1}
          max={5000}
          onChange={(v) => set({ generations: v })}
          disabled={disabled}
        />
        <Field
          label="Mutation rate"
          sublabel="Per-gene perturbation"
          value={config.mutation_rate}
          step={0.01}
          min={0}
          max={1}
          onChange={(v) => set({ mutation_rate: v })}
          disabled={disabled}
        />
        <Field
          label="Crossover rate"
          sublabel="Recombination probability"
          value={config.crossover_rate}
          step={0.01}
          min={0}
          max={1}
          onChange={(v) => set({ crossover_rate: v })}
          disabled={disabled}
        />
        <Field
          label="Tournament size (K)"
          sublabel="Selection contenders"
          value={config.tournament_size}
          min={2}
          max={20}
          onChange={(v) => set({ tournament_size: v })}
          disabled={disabled}
        />
        <Field
          label="Elite count (E)"
          sublabel="Guaranteed survivors"
          value={config.elite_count}
          min={0}
          max={50}
          onChange={(v) => set({ elite_count: v })}
          disabled={disabled}
        />
        <Field
          label="Stagnation limit"
          sublabel="Early stop plateau"
          value={config.stagnation_limit ?? 40}
          min={1}
          max={500}
          onChange={(v) => set({ stagnation_limit: v })}
          disabled={disabled}
        />
        <Field
          label="Random seed"
          sublabel="0 = non-deterministic"
          value={config.random_seed ?? 0}
          min={0}
          onChange={(v) => set({ random_seed: v === 0 ? null : v })}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
