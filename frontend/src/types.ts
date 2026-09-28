export interface Subject {
  subject_id: string;
  name: string;
  faculty_id: string;
  batch_id: string;
  sessions_per_week: number;
  expected_students: number;
  preferred_room_type?: string | null;
}

export interface Faculty {
  faculty_id: string;
  name: string;
  department: string;
}

export interface Room {
  room_id: string;
  room_number: string;
  capacity: number;
  room_type: string;
}

export interface Batch {
  batch_id: string;
  name: string;
  student_count: number;
}

export interface DatasetInput {
  subjects: Subject[];
  faculty: Faculty[];
  rooms: Room[];
  batches: Batch[];
  days: string[];
  periods_per_day: number;
}

export interface GAConfig {
  population_size: number;
  generations: number;
  mutation_rate: number;
  crossover_rate: number;
  tournament_size: number;
  elite_count: number;
  stagnation_limit: number | null;
  random_seed: number | null;
  hard_faculty_conflict: number;
  hard_student_conflict: number;
  hard_room_conflict: number;
  capacity_violation: number;
  faculty_gap: number;
  student_gap: number;
  distribution_penalty: number;
}

export const DEFAULT_CONFIG: GAConfig = {
  population_size: 100,
  generations: 200,
  mutation_rate: 0.1,
  crossover_rate: 0.8,
  tournament_size: 3,
  elite_count: 5,
  stagnation_limit: 40,
  random_seed: null,
  hard_faculty_conflict: 1000,
  hard_student_conflict: 1000,
  hard_room_conflict: 1000,
  capacity_violation: 500,
  faculty_gap: 10,
  student_gap: 10,
  distribution_penalty: 5,
};

export interface GeneOut {
  subject_id: string;
  subject_name: string;
  faculty_id: string;
  faculty_name: string;
  batch_id: string;
  batch_name: string;
  room_id: string;
  room_number: string;
  day: string;
  period: number;
}

export interface GenerationStat {
  generation: number;
  best_fitness: number;
  avg_fitness: number;
  best_cost: number;
  hard_violations: number;
  soft_penalty: number;
}

export interface ConstraintReport {
  faculty_conflicts: number;
  student_conflicts: number;
  room_conflicts: number;
  capacity_violations: number;
  faculty_gaps: number;
  student_gaps: number;
  distribution_penalties: number;
}

export interface InitialMetrics {
  hard_violations: number;
  soft_violations: number;
  faculty_conflicts: number;
  student_conflicts: number;
  room_conflicts: number;
  capacity_violations: number;
  faculty_gaps: number;
  student_gaps: number;
  distribution_penalties: number;
  total_cost: number;
  fitness: number;
}

export interface OptimizeResponse {
  timetable: GeneOut[];
  history: GenerationStat[];
  final_cost: number;
  final_fitness: number;
  constraints: ConstraintReport;
  generations_executed: number;
  execution_time_seconds: number;
  population_size: number;
  converged_early: boolean;
  initial_metrics?: InitialMetrics | null;
}
