from datetime import date, timedelta
from config import GEMINI_API_KEY, AI_MODEL


class AIAnalyzer:

    def __init__(self):
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                self._model = genai.GenerativeModel(AI_MODEL)
            except Exception as e:
                print(f"[AI] Error initializing model: {e}")
                return None
        return self._model

    def analyze_day(self, report_date=None):
        from features.reports import report_generator

        if report_date is None:
            report_date = date.today()

        report = report_generator.daily_report(report_date)

        prompt = self._build_daily_prompt(report)
        insights = self._query_llm(prompt)

        if insights:
            self._save_insights(report_date, insights)

        return {
            "date": report_date.isoformat(),
            "insights": insights,
            "report": report,
        }

    def analyze_week(self):
        """Analyze the past week's productivity trends."""
        from features.reports import report_generator

        report = report_generator.weekly_report()
        prompt = self._build_weekly_prompt(report)
        insights = self._query_llm(prompt)

        return {
            "period": report.get("period"),
            "insights": insights,
        }

    def chat(self, question):
        """Ask a question about productivity data."""
        from features.reports import report_generator

        context_data = []
        for i in range(3):
            d = date.today() - timedelta(days=i)
            context_data.append(report_generator.daily_report(d))

        prompt = f"""You are FoxFlow AI, a productivity analysis assistant. 
You have access to the user's productivity tracking data from the last 3 days.

Data:
{self._format_data(context_data)}

User question: {question}

Provide a helpful, concise answer based on the data. Be specific with numbers and times.
If the data doesn't contain enough information to answer, say so honestly.
Use a friendly, encouraging tone. Format your response with markdown."""

        return {
            "question": question,
            "answer": self._query_llm(prompt) or "Unable to generate response. Please check your API key.",
        }

    def _build_daily_prompt(self, report):
        return f"""You are FoxFlow AI, a productivity analysis assistant.
Analyze this daily productivity report and provide actionable insights.

Date: {report.get('date')}

Eye Tracking:
- Focus time: {report.get('eye_tracking', {}).get('focus_minutes', 0)} minutes
- Away time: {report.get('eye_tracking', {}).get('away_minutes', 0)} minutes
- Focus ratio: {report.get('eye_tracking', {}).get('focus_percent', 0)}%

Top Applications:
{self._format_list(report.get('top_apps', []), 'name', 'minutes')}

Top Websites:
{self._format_list(report.get('top_websites', []), 'domain', 'minutes')}

Input Activity:
- Keystrokes: {report.get('input', {}).get('keystrokes', 0)}
- Mouse clicks: {report.get('input', {}).get('mouse_clicks', 0)}

Focus Scores by Hour:
{self._format_hourly(report.get('focus', {}).get('hourly', []))}

Average Focus Score: {report.get('focus', {}).get('average_score', 0)}/100
Pomodoros Completed: {report.get('pomodoros_completed', 0)}
Goals Met: {report.get('goals_met', 0)}/{report.get('total_goals', 0)}

Please provide:
1. **Overall Assessment** — How productive was this day? (1-2 sentences)
2. **Peak Performance** — When was the user most focused and what were they doing?
3. **Distraction Patterns** — Any distracting websites/apps? When did focus dip?
4. **Recommendations** — 2-3 specific, actionable tips for tomorrow
5. **Encouragement** — One positive thing about today's performance

Keep the response concise and use markdown formatting with emojis."""

    def _build_weekly_prompt(self, report):
        daily = report.get("daily_breakdown", [])
        summary_lines = []
        for d in daily:
            summary_lines.append(
                f"- {d.get('date')}: Focus={d.get('focus', {}).get('average_score', 0)}/100, "
                f"Screen={d.get('eye_tracking', {}).get('focus_minutes', 0)}min, "
                f"Pomodoros={d.get('pomodoros_completed', 0)}"
            )

        return f"""You are FoxFlow AI. Analyze this weekly productivity summary.

Period: {report.get('period')}
Total Focus Hours: {report.get('total_focus_hours')}
Average Daily Focus Score: {report.get('avg_daily_focus_score')}/100
Total Pomodoros: {report.get('total_pomodoros')}
Peak Day: {report.get('peak_day')} (score: {report.get('peak_score')})

Daily Breakdown:
{chr(10).join(summary_lines)}

Provide:
1. **Weekly Overview** — Overall trend (improving, declining, stable?)
2. **Best & Worst Days** — What made the difference?
3. **Patterns** — Any recurring patterns (specific days/hours)?
4. **Weekly Score** — Rate the week 1-10 with brief justification
5. **Next Week Goals** — 2-3 goals for improvement

Keep concise, use markdown with emojis."""

    def _query_llm(self, prompt):
        if not GEMINI_API_KEY:
            return self._mock_response()

        model = self._get_model()
        if not model:
            return self._mock_response()

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[AI] Query error: {e}")
            return self._mock_response()

    def _mock_response(self):
        return """## 🦊 FoxFlow AI Insights

> **Note**: AI analysis requires a Gemini API key. Set the `GEMINI_API_KEY` environment variable to enable full AI insights.

### Quick Summary
Based on your tracked data, here's what we can see:
- 📊 Your focus data is being collected and stored
- ⏱️ Tracking is active and recording your sessions
- 🎯 Set up your API key to unlock personalized AI insights about your productivity patterns!


    def _format_list(self, items, name_key, value_key):
        if not items:
            return "  No data"
        return "\n".join(f"  - {item[name_key]}: {item[value_key]} min" for item in items[:5])

    def _format_hourly(self, hourly):
        if not hourly:
            return "  No data"
        return "\n".join(f"  - {h['hour']:02d}:00 — Score: {h['score']}" for h in hourly)

    def _format_data(self, reports):
        lines = []
        for r in reports:
            lines.append(f"Date: {r.get('date')}")
            lines.append(f"  Focus: {r.get('focus', {}).get('average_score', 0)}/100")
            lines.append(f"  Screen: {r.get('eye_tracking', {}).get('focus_minutes', 0)}min")
            lines.append(f"  Pomodoros: {r.get('pomodoros_completed', 0)}")
        return "\n".join(lines)

    def _save_insights(self, report_date, insights):
        try:
            from db.database import SessionLocal
            from db.models import DailyReport

            db = SessionLocal()
            try:
                existing = db.query(DailyReport).filter_by(date=report_date).first()
                if existing:
                    existing.ai_insights = insights
                else:
                    report = DailyReport(date=report_date, ai_insights=insights)
                    db.add(report)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[AI] Save error: {e}")


# Singleton
ai_analyzer = AIAnalyzer()
