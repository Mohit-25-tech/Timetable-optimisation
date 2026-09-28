import type { GAConfig } from "../types";

interface Props {
  config?: GAConfig;
}

const PIPELINE_STEPS = [
  { label: "Input Data", desc: "Curriculum requirements (30 subjects, 90 sessions)" },
  { label: "Chromosome", desc: "List of 90 session genes: (subj, fac, batch, room, day, period)" },
  { label: "Population", desc: "Set of candidate chromosomes (size = N)" },
  { label: "Fitness Evaluation", desc: "Calculated as 1 / (1 + Total Cost)" },
  { label: "Tournament Selection", desc: "Sample K candidates, choose fittest parent" },
  { label: "Two-Point Crossover", desc: "Swap (room, day, period) segment between cut points" },
  { label: "Mutation", desc: "Random slot change, room change, or slot swap" },
  { label: "Constraint Repair", desc: "Bounded local search (max 8 attempts) to clear conflicts" },
  { label: "Elitism", desc: "Preserve top E individuals unchanged into next gen" },
  { label: "Next Generation", desc: "Form new population for subsequent iteration" },
  { label: "Termination", desc: "Stagnation plateau with 0 hard violations or max gens" },
  { label: "Best Feasible Timetable", desc: "Conflict-free schedule exported & visualized" },
];

export default function AlgorithmExplainer({ config }: Props) {
  const k = config?.tournament_size ?? 3;
  const elites = config?.elite_count ?? 5;
  const mutRate = config?.mutation_rate ?? 0.1;
  const crossRate = config?.crossover_rate ?? 0.8;

  return (
    <div className="card explainer-card">
      <div className="card-header-row">
        <h2>How the Genetic Algorithm Works</h2>
        <span className="dataset-tag">Academic Architecture &amp; Viva Reference</span>
      </div>

      <p className="explainer-intro">
        This system solves the university course timetabling problem using a custom, from-scratch Constraint-Aware
        Genetic Algorithm (implemented in Python without any black-box solver). Follow the pipeline and expand each section below
        for the exact mathematical and algorithmic details implemented in this codebase.
      </p>

      {/* PIPELINE FLOWCHART */}
      <div className="pipeline-flowchart">
        {PIPELINE_STEPS.map((step, idx) => (
          <div key={step.label} className="pipeline-step-wrapper">
            <div className="pipeline-step-node">
              <span className="step-number">{idx + 1}</span>
              <span className="step-name">{step.label}</span>
            </div>
            {idx < PIPELINE_STEPS.length - 1 && (
              <span className="pipeline-arrow" aria-hidden="true">→</span>
            )}
          </div>
        ))}
      </div>

      <div className="accordion-group">
        {/* 1. CHROMOSOME REPRESENTATION */}
        <details className="explain-accordion" open>
          <summary>
            <span className="summary-title">1. Chromosome &amp; Population Representation</span>
            <span className="summary-badge">Data Structure</span>
          </summary>
          <div className="explain-body">
            <p>
              In our codebase (<code>backend/optimizer/chromosome.py</code>), the representation is carefully partitioned
              between fixed curriculum constraints and searchable scheduling decisions:
            </p>
            <ul>
              <li>
                <strong>Gene Structure:</strong> A gene is one scheduled class session:
                <pre className="code-block">
{`Gene = {
    "subject_id": str,   # Fixed curriculum requirement
    "faculty_id": str,   # Fixed instructor assignment
    "batch_id":   str,   # Fixed student cohort
    "room_id":    str,   # Search decision (room assignment)
    "day":        str,   # Search decision ("Mon".."Fri")
    "period":     int    # Search decision (1..6)
}`}
                </pre>
                Because <code>(subject_id, faculty_id, batch_id)</code> is determined by the academic syllabus, it remains
                immutable throughout the evolutionary cycle. The Genetic Algorithm <em>only searches over</em> the{" "}
                <code>(room_id, day, period)</code> assignment.
              </li>
              <li>
                <strong>Chromosome:</strong> An ordered list of exactly <strong>90 genes</strong>, corresponding to all required
                weekly sessions across the curriculum. Each chromosome represents one complete candidate timetable for the entire university.
              </li>
              <li>
                <strong>Population:</strong> A list of <em>N</em> candidate chromosomes (default: <code>population_size = 100</code>)
                evaluated and evolved generation by generation.
              </li>
            </ul>
          </div>
        </details>

        {/* 2. FITNESS FUNCTION */}
        <details className="explain-accordion" open>
          <summary>
            <span className="summary-title">2. Fitness Function &amp; Mathematical Objective</span>
            <span className="summary-badge">Evaluation Model</span>
          </summary>
          <div className="explain-body">
            <p>
              The objective function (<code>backend/optimizer/fitness.py</code>) evaluates each timetable by computing a weighted
              penalty cost across all hard and soft constraint violations, and then inverts the cost so that lower penalties yield higher fitness:
            </p>
            <div className="formula-box">
              <div className="formula-line">
                <strong>Total Cost</strong> ={" "}
                <span className="hard-weight">1,000 × Faculty Conflicts</span> +{" "}
                <span className="hard-weight">1,000 × Student/Batch Conflicts</span> +{" "}
                <span className="hard-weight">1,000 × Room Conflicts</span> +{" "}
                <span className="hard-weight">500 × Capacity Violations</span> +{" "}
                <span className="soft-weight">10 × Faculty Idle Gaps</span> +{" "}
                <span className="soft-weight">10 × Student Idle Gaps</span> +{" "}
                <span className="soft-weight">5 × Subject Distribution Penalties</span>
              </div>
              <div className="formula-line" style={{ marginTop: 8 }}>
                <strong>Fitness</strong> = <code>1.0 / (1.0 + Total Cost)</code>
              </div>
            </div>
            <p style={{ marginTop: 10 }}>
              <strong>Why Hard Weights Dominate Soft Weights:</strong> Hard-constraint penalties (1,000 and 500)
              are two orders of magnitude greater than soft-constraint penalties (10 and 5). By design, even a single hard collision
              (e.g., a professor double-booked) adds 1,000 to the cost, ensuring that the evolutionary selection pressure strictly
              prefers any feasible schedule over an infeasible schedule with zero gaps.
            </p>
          </div>
        </details>

        {/* 3. SELECTION, CROSSOVER, MUTATION */}
        <details className="explain-accordion">
          <summary>
            <span className="summary-title">3. Genetic Operators (Selection, Crossover &amp; Mutation)</span>
            <span className="summary-badge">Evolutionary Mechanics</span>
          </summary>
          <div className="explain-body">
            <p>
              The operators in <code>backend/optimizer/operators.py</code> are specialized for timetabling:
            </p>
            <ul>
              <li>
                <strong>Tournament Selection (K = {k}):</strong> To pick each parent, <em>K</em> candidate timetables are sampled uniformly
                at random from the current population. The candidate with the highest fitness wins the tournament and is selected for reproduction.
                This provides adjustable selection pressure without premature convergence.
              </li>
              <li>
                <strong>Two-Point Crossover (Rate = {(crossRate * 100).toFixed(0)}%):</strong> Because chromosome length is fixed and gene order is aligned
                (all chromosomes list the same required curriculum sessions in identical sequence), two random cut points <em>p1</em> and <em>p2</em> are selected.
                The <code>(room, day, period)</code> assignment segment between <em>p1</em> and <em>p2</em> is swapped between the parents.
                Crucially, this guarantees that no class session is ever duplicated or lost; every required class remains present.
              </li>
              <li>
                <strong>Mutation (Rate = {(mutRate * 100).toFixed(0)}%):</strong> Each gene independently mutates with probability <code>mutation_rate</code>.
                When triggered, one of three perturbation moves is executed at random:
                <ol>
                  <li><em>Slot move:</em> Assigns a new random <code>(day, period)</code>.</li>
                  <li><em>Room move:</em> Reassigns the session to a different random room.</li>
                  <li><em>Swap move:</em> Swaps <code>(day, period, room)</code> slots with another random gene in the chromosome.</li>
                </ol>
                This injects diversity and allows the algorithm to escape local minima.
              </li>
            </ul>
          </div>
        </details>

        {/* 4. REPAIR & ELITISM */}
        <details className="explain-accordion">
          <summary>
            <span className="summary-title">4. Constraint Repair &amp; Elitism Strategy</span>
            <span className="summary-badge">Feasibility Preservation</span>
          </summary>
          <div className="explain-body">
            <ul>
              <li>
                <strong>Bounded-Attempt Constraint Repair:</strong> Crossover and mutation can introduce faculty, room, or batch double-booking.
                Immediately following mutation, a local repair pass (<code>repair()</code>) inspects the chromosome for conflicting occupants
                and room capacity breaches. For each conflicted gene, repair attempts up to <strong>8 random candidate slots</strong> that are currently free
                for that faculty, batch, and room with sufficient capacity. The attempt limit prevents infinite loops; any unresolved collisions
                are naturally penalized by the fitness function.
              </li>
              <li>
                <strong>Elitism (Top {elites} Individuals):</strong> At the beginning of each generation, the top <code>elite_count</code>{" "}
                individuals with the lowest cost are copied directly into the new generation unchanged. This guarantees monotonic quality preservation:
                the best solution discovered so far can never be degraded or lost by stochastic operators.
              </li>
            </ul>
          </div>
        </details>

        {/* 5. WHY NOT GRADIENT DESCENT */}
        <details className="explain-accordion">
          <summary>
            <span className="summary-title">5. Theoretical Basis: Why Not Gradient Descent?</span>
            <span className="summary-badge">Combinatorial Complexity</span>
          </summary>
          <div className="explain-body">
            <p>
              University course timetabling is a classical <strong>discrete combinatorial optimization problem</strong> (NP-hard in the general case).
              Gradient-based optimization methods (like Gradient Descent, Adam, or L-BFGS) cannot be applied directly for fundamental mathematical reasons:
            </p>
            <ol>
              <li>
                <strong>Categorical &amp; Discrete Search Variables:</strong> Variables such as day of the week (<code>Mon..Fri</code>),
                class period (<code>1..6</code>), and room ID (<code>LT-1..SR-10</code>) are discrete categorical assignments. There is no continuous coordinate space
                to compute partial derivatives.
              </li>
              <li>
                <strong>Non-Differentiable Penalty Landscape:</strong> The objective function is piecewise constant and penalty-based: a constraint is either satisfied
                (0 penalty) or violated (step jump of +1,000). The gradient is zero almost everywhere and undefined at boundaries, rendering gradient descent useless.
              </li>
              <li>
                <strong>Direct Permutation Navigation:</strong> Genetic Algorithms do not require derivative information. Instead, they navigate the discrete
                search landscape through stochastic sampling, recombination of promising sub-schedules (building blocks), targeted local repair, and diversity maintenance.
              </li>
            </ol>
            <p className="academic-disclaimer">
              <em>Note for viva defense:</em> A Genetic Algorithm is a heuristic optimization technique. It is designed to reliably converge on a{" "}
              <strong>high-quality, feasible solution</strong> that satisfies all physical constraints and optimizes soft preferences,
              without falsely claiming mathematical global optimality over an intractable combinatorial space.
            </p>
          </div>
        </details>
      </div>
    </div>
  );
}
