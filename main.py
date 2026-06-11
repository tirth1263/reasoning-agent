"""Simple Reasoning Agent.

Run a financial reasoning agent powered by Agno and Nebius.
"""

from __future__ import annotations

import argparse
import os
from textwrap import dedent

from agno.agent import Agent
from agno.models.nebius import Nebius
from dotenv import load_dotenv


DEFAULT_PROMPT = (
    "Recommend an investment strategy for a client with moderate risk tolerance"
)
DEFAULT_MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"


def assess_risk_profile(
    risk_tolerance: str,
    investment_horizon_years: int = 10,
    liquidity_needs: str = "moderate",
) -> str:
    """Assess an investor risk profile from core planning variables.

    Args:
        risk_tolerance: Investor risk tolerance, such as low, moderate, or high.
        investment_horizon_years: Approximate number of years before funds are needed.
        liquidity_needs: Expected need for near-term cash access.
    """
    tolerance_scores = {"low": 1, "conservative": 1, "moderate": 3, "high": 5}
    liquidity_penalty = {"low": 0, "moderate": 1, "high": 2}

    normalized_tolerance = risk_tolerance.strip().lower()
    normalized_liquidity = liquidity_needs.strip().lower()
    base_score = tolerance_scores.get(normalized_tolerance, 3)
    horizon_adjustment = 1 if investment_horizon_years >= 10 else -1
    penalty = liquidity_penalty.get(normalized_liquidity, 1)
    score = max(1, min(5, base_score + horizon_adjustment - penalty))

    if score <= 2:
        profile = "conservative"
    elif score == 3:
        profile = "balanced"
    else:
        profile = "growth-oriented"

    return dedent(
        f"""
        Risk profile: {profile}
        Risk score: {score}/5
        Key drivers: stated tolerance={risk_tolerance}, horizon={investment_horizon_years} years,
        liquidity needs={liquidity_needs}.
        Interpretation: use this as a planning input, then confirm income stability,
        debt levels, emergency savings, tax situation, and investment constraints.
        """
    ).strip()


def suggest_asset_allocation(
    risk_profile: str,
    investment_horizon_years: int = 10,
) -> str:
    """Suggest a broad educational asset allocation for a risk profile.

    Args:
        risk_profile: Investor profile, such as conservative, balanced, or growth-oriented.
        investment_horizon_years: Approximate number of years before funds are needed.
    """
    normalized_profile = risk_profile.strip().lower()

    if "conservative" in normalized_profile:
        allocation = {
            "stocks": 30,
            "bonds": 55,
            "cash_or_short_term": 10,
            "alternatives": 5,
        }
    elif "growth" in normalized_profile or investment_horizon_years >= 15:
        allocation = {
            "stocks": 70,
            "bonds": 20,
            "cash_or_short_term": 5,
            "alternatives": 5,
        }
    else:
        allocation = {
            "stocks": 50,
            "bonds": 35,
            "cash_or_short_term": 10,
            "alternatives": 5,
        }

    return dedent(
        f"""
        Suggested allocation:
        - Stocks: {allocation["stocks"]}%
        - Bonds: {allocation["bonds"]}%
        - Cash or short-term reserves: {allocation["cash_or_short_term"]}%
        - Diversifying alternatives: {allocation["alternatives"]}%

        Rationale: match the risk budget to the time horizon, keep enough liquid assets
        for near-term needs, and diversify across return drivers.
        """
    ).strip()


def stress_test_portfolio(
    stock_weight: int,
    bond_weight: int,
    cash_weight: int,
    alternatives_weight: int = 0,
) -> str:
    """Check whether a proposed allocation is balanced and easy to rebalance.

    Args:
        stock_weight: Percentage allocated to stocks.
        bond_weight: Percentage allocated to bonds.
        cash_weight: Percentage allocated to cash or short-term reserves.
        alternatives_weight: Percentage allocated to alternatives or other assets.
    """
    total = stock_weight + bond_weight + cash_weight + alternatives_weight
    risk_notes = []

    if total != 100:
        risk_notes.append(f"Allocation totals {total}%, so it should be normalized.")
    if stock_weight > 70:
        risk_notes.append("Stock exposure is high and may create large drawdowns.")
    if cash_weight < 5:
        risk_notes.append("Cash reserve is thin for unexpected liquidity needs.")
    if bond_weight < 20 and stock_weight >= 60:
        risk_notes.append("Bond ballast may be too small for a moderate investor.")
    if not risk_notes:
        risk_notes.append("Allocation is internally consistent for a diversified plan.")

    return dedent(
        f"""
        Portfolio check:
        - Total allocation: {total}%
        - Stocks: {stock_weight}%
        - Bonds: {bond_weight}%
        - Cash or short-term reserves: {cash_weight}%
        - Alternatives: {alternatives_weight}%
        - Review notes: {" ".join(risk_notes)}
        - Rebalancing guide: review quarterly and rebalance when any major sleeve drifts
          more than 5 percentage points from target.
        """
    ).strip()


def build_agent() -> Agent:
    """Create the Agno financial reasoning agent."""
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NEBIUS_API_KEY is missing. Add it to a .env file or export it before running."
        )

    model_id = os.getenv("NEBIUS_MODEL_ID", DEFAULT_MODEL_ID)

    return Agent(
        name="Simple Reasoning Agent",
        role="Expert financial advisor for educational investment planning",
        model=Nebius(id=model_id, api_key=api_key),
        tools=[
            assess_risk_profile,
            suggest_asset_allocation,
            stress_test_portfolio,
        ],
        reasoning=True,
        reasoning_min_steps=3,
        reasoning_max_steps=6,
        markdown=True,
        add_datetime_to_context=True,
        instructions=[
            "Break every investment question into assumptions, key variables, analysis, risks, alternatives, and a final recommendation.",
            "Use the provided tools when risk profile, asset allocation, or portfolio checks would make the answer more rigorous.",
            "Show user-facing reasoning steps, but keep them concise and decision-focused.",
            "Avoid promises of returns. Discuss uncertainty, trade-offs, diversification, and rebalancing.",
            "End with an educational disclaimer that this is not personalized financial advice.",
        ],
        expected_output=dedent(
            """
            A structured financial recommendation with:
            1. Assumptions
            2. Reasoning steps
            3. Tool-supported analysis
            4. Risks and alternatives
            5. Final recommendation
            """
        ).strip(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an Agno reasoning agent for investment strategy questions."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="Investment question to ask the reasoning agent.",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streamed terminal output.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Show the final answer with compact reasoning instead of full reasoning details.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    agent = build_agent()

    agent.print_response(
        args.prompt,
        stream=not args.no_stream,
        show_message=True,
        show_reasoning=args.compact,
        show_full_reasoning=not args.compact,
    )


if __name__ == "__main__":
    main()
