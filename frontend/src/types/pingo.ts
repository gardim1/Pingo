export interface DecisionTerms {
  label?: string | null;
  total_price_cents?: number | null;
  upfront_cents?: number | null;
  installment_count?: number | null;
  interest_free?: boolean | null;
  first_due_date?: string | null;
  purchase_month?: string | null;
}

export interface HistoricalComparison {
  month: string;
  conditional_release_cents: number;
  benchmark_margin_cents: number;
  margin_after_installment_min_cents: number | null;
  margin_after_installment_max_cents: number | null;
}

export interface GoldenAnalysis {
  reference_date: string;
  data_source: string;
  salary_observed_cents: number | null;
  recent_average_margin_cents: number | null;
  six_month_average_margin_cents: number | null;
  last_month_margin_cents: number | null;
  observed_installments_total_cents: number;
  observed_installment_count: number;
  estimated_last_installment_month: string | null;
  installments_cents: number[];
  selected_month: string;
  selected_conditional_release_cents: number;
  comparisons: HistoricalComparison[];
  assumptions: string[];
  simulated_purchase_cents?: number;
  event_month_before_cents?: number | null;
  event_month_after_cents?: number | null;
}

export interface Question {
  field: string;
  text: string;
}

export interface ScenarioScheduleItem {
  due_date: string;
  amount_cents: number;
  kind?: string;
  label?: string;
}

export interface Scenario {
  title: string;
  total_price_cents: number;
  upfront_cents: number;
  schedule: ScenarioScheduleItem[];
  visible_until?: string | null;
  remaining_after_window_cents?: number;
  projection?: {
    assessment?: string;
    min_balance_cents?: number | null;
    violated_rule?: string | null;
  };
}

export interface DecisionResponse {
  state: string;
  as_of_date: string;
  data_mode: string;
  scenarios: Scenario[];
  question?: Question | null;
  actions?: string[];
  assumptions: string[];
  evidence?: Array<{ id: string; label: string; origin: string; detail?: string }>;
  message?: string;
  request_id?: string;
}

export interface ChatResponse {
  session_id: string;
  decision?: DecisionResponse | null;
  draft?: DecisionTerms | null;
  golden_analysis?: GoldenAnalysis | null;
  runtime?: {
    agent: string;
    model?: string | null;
    data: string;
    safety?: string;
  };
  error?: string | null;
  message: string;
}

export interface AccompanimentResponse {
  reviewed: boolean;
  reason: string;
  decision?: DecisionResponse | null;
  plan_id?: string | null;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'pingo';
  text: string;
  time: string;
  analysis?: GoldenAnalysis | null;
  draft?: DecisionTerms | null;
  decision?: DecisionResponse | null;
  questionField?: string | null;
  chips?: Array<{ label: string; action: () => void }>;
  simulatedEvent?: boolean;
}
