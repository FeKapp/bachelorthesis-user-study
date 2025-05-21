# bachelorthesis-user-study

**Human Behavior with AI-based Financial Investment Recommendations**

This repository contains the web application and user-study interface for the bachelor thesis investigating how humans interact with AI-generated (balanced and unbalanced) investment advice. Participants allocate their hypothetical assets between two funds (Fund A and Fund B), receive AI recommendations, adjust their allocations, and view performance outcomes. In the end, a final long-term investment decision is taken to assess moypic loss aversion.

---

## Key Features

- **Interactive Experiment Flow**: Consent form → Instructions → Demo steps → Repeated trial rounds → Final allocation → Debriefing and demographics.
- **AI Recommendations**: Preset AI allocations per trial to compare human vs AI decisions.
- **Performance Visualization**: Charts showing portfolio performance, AI vs user allocations, and fund returns.
- **Data Persistence**: Participant sessions, allocations, returns, and demographics are stored in Supabase.
- **Streamlit Deployment**: Easy hosting and sharing via Streamlit.

---

## Prerequisites

- Python 3.11+
- `pip` for dependency management
- Supabase account (free tier sufficient)
- Streamlit account (for deployment)

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FeKapp/bachelorthesis-user-study.git
   cd bachelorthesis-user-study
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the project root with the following keys:
   ```dotenv
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_or_service_role_key
   ```
   Streamlit will automatically load these on startup. Also configure the same variables in your Streamlit app settings when deploying.

---

## Database Schema & Setup

Use the following SQL to initialize your Supabase database. You can execute these statements in the Supabase SQL editor.

```sql
-- Configuration Tables
CREATE TABLE scenario_config (
  scenario_id uuid PRIMARY KEY,
  scenario_name text UNIQUE NOT NULL,
  ai_type text NOT NULL,
  num_trials integer NOT NULL,
  periods_per_trial integer NOT NULL,
  description text
);

-- Pre-generated Data Tables
CREATE TABLE fund_returns (
  fund_return_id uuid PRIMARY KEY,
  scenario_id uuid REFERENCES scenario_config(scenario_id),
  trial_number integer NOT NULL,
  return_a float NOT NULL,
  return_b float NOT NULL,
  UNIQUE(scenario_id, trial_number)
);

CREATE TABLE ai_recommendations (
  recommendation_id uuid PRIMARY KEY,
  scenario_id uuid REFERENCES scenario_config(scenario_id),
  trial_number integer NOT NULL,
  fund_a float NOT NULL,
  fund_b float NOT NULL,
  UNIQUE(scenario_id, trial_number)
);

-- Core Experiment Tables
CREATE TABLE trial_sequences (
  trial_sequence_id UUID PRIMARY KEY,
  five_year_trials INT[] NOT NULL,
  three_month_trials INT[] NOT NULL
);

CREATE TABLE sessions (
  session_id uuid PRIMARY KEY,
  scenario_id uuid REFERENCES scenario_config(scenario_id),
  trial_sequence_id uuid REFERENCES trial_sequences(trial_sequence_id),
  current_page text,
  current_trial integer,
  current_trial_step integer,
  max_trials integer,
  consent_given boolean DEFAULT FALSE,
  instructed_response_2_passed boolean,
  data_quality boolean,
  data_quality_comment text,
  created_at timestamptz,
  completed_at timestamptz
);

CREATE TABLE trials (
  trial_id uuid PRIMARY KEY,
  session_id uuid REFERENCES sessions(session_id),
  trial_number integer,
  return_a float,
  return_b float,
  created_at timestamptz
);

CREATE TABLE allocations (
  allocation_id uuid PRIMARY KEY,
  trial_id uuid REFERENCES trials(trial_id),
  allocation_type text,
  fund_a float,
  fund_b float,
  portfolio_return float,
  created_at timestamptz
);

CREATE TABLE demographics (
  demographic_id uuid PRIMARY KEY,
  session_id uuid REFERENCES sessions(session_id),
  gender text,
  age integer,
  country text,
  education_level text,
  ai_proficiency integer,
  financial_literacy integer,
  created_at timestamptz DEFAULT NOW()
);
```

---

## Running Locally

1. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```
2. **Access** the app at `http://localhost:8501/`.
3. **Follow** the on-screen instructions to participate in the study.

---

## Deployment on Streamlit

To deploy to Streamlit Cloud:

1. **Push** your repository to GitHub.
2. **Connect** the repo in your Streamlit account dashboard.
3. **Set** your `SUPABASE_URL` and `SUPABASE_KEY` in the app's Secrets.
4. **Deploy**; the app will be publicly available at `https://your-app-name.streamlit.app`.


*Happy Experimenting!*
