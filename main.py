import pandas as pd
import matplotlib.pyplot as plt

# convert churn to numeric
def convert_churn_to_numeric(df):
    df["ChurnFlag"] = df["Churn"].map({"Yes": 1, "No": 0})
    return df

# plot monthly charges distribution by churn status
def plot_monthly_charges_distribution(df):
    plt.figure(figsize=(8,5))
    df[df["Churn"] == "No"]["MonthlyCharges"].plot(kind="hist", alpha=0.6, bins=30, label="No Churn")
    df[df["Churn"] == "Yes"]["MonthlyCharges"].plot(kind="hist", alpha=0.6, bins=30, label="Churn")

    plt.title("Monthly Charges Distribution: Churn vs No Churn")
    plt.xlabel("Monthly Charges")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.show()

# compute overall churn probability
def compute_overall_churn_probability(df):
    return df["ChurnFlag"].mean()
# compute chun probabilikty by contract type
def churn_probability_by_contract(df):
    contract_probs = df.groupby("Contract")["ChurnFlag"].mean()
    return contract_probs
# create buckets for churn probability by monthlycharges
# based on the histogram, three buckets. low = 0-40, medium = 40-70, high = 70+
def churn_probability_by_charge_bucket(df):
    bins = [0, 40,70, df["MonthlyCharges"].max()]
    labels = ["Low", "Medium", "High"]
    df["ChargeBucket"] = pd.cut(df["MonthlyCharges"], bins=bins, labels=labels, include_lowest=True)
    bucket_probs = df.groupby("ChargeBucket", observed=False)["ChurnFlag"].mean()
    return bucket_probs


# churn risk score function, assign risk score to df
def assign_risk_score(df):
    contract_scores = {
        "Month-to-month": 2,
        "One year": 1,
        "Two year": 0
    }
    charge_scores = {
        "Low": 0,
        "Medium": 1,
        "High": 2
    }
    df["ContractRisk"] = df["Contract"].map(contract_scores).astype(int)
    df["ChargeRisk"] = df["ChargeBucket"].map(charge_scores).astype(int)
    # final overall risk, 0 to 4
    df["RiskScore"] = df["ContractRisk"] + df["ChargeRisk"]
    return df

# compute churn probability by risk score
def evaluate_risk_score(df):
    risk_churn = df.groupby("RiskScore")["ChurnFlag"].mean()
    print("\nChurn Probability by RiskScore: ")
    print(risk_churn)

# find expected value for each risk score
def compute_expected_value(df, offer_cost):
    # churn probability by risk score
    churn_probs = df.groupby("RiskScore")["ChurnFlag"].mean()
    # compute average customer value by risk score (using monthl charges)
    avg_value = df.groupby("RiskScore")["MonthlyCharges"].mean()
    # compute expected value for each score
    ev = (churn_probs * avg_value) - offer_cost

    results = pd.DataFrame({
        "Churn Probability": churn_probs,
        "Average Monthly Charge": avg_value,
        "Expected Value": ev
    })
    print("\nExpected Value Table")
    print(results)
    #return results

# cost sensitivity analysis
def compute_cost_sensitivity(df, cost_list):
    results = []
    churn_probs = df.groupby("RiskScore")["ChurnFlag"].mean()
    avg_value = df.groupby("RiskScore")["MonthlyCharges"].mean()
    for cost in cost_list:
        ev = (churn_probs * avg_value) - cost

        for score in ev.index:
            results.append({
                "OfferCost": cost,
                "RiskScore": score,
                "ChurnProb": churn_probs[score],
                "AvgMonthlyCharge": avg_value[score],
                "ExpectedValue": ev[score]
            })

    results_df = pd.DataFrame(results)
    print("\nCost Sensitivity Table")
    print(results_df)
    #return results_df                                        

# ev vs risk score plot
def plot_ev_by_risk(df, cost_list):
    churn_probs = df.groupby("RiskScore")["ChurnFlag"].mean()
    avg_value = df.groupby("RiskScore")["MonthlyCharges"].mean()
    plt.figure(figsize=(10,6))
    for cost in cost_list:
        ev = (churn_probs * avg_value) - cost
        plt.plot(ev.index, ev.values, marker = 'o', label= f"Cost= ${cost}")
    plt.axhline(0, color='black', linewidth=1, linestyle = '--')
    plt.xlabel("Risk Score")
    plt.ylabel("Expected Value ($)")
    plt.title("Expected Value vs Risk Score for Different Offer Costs")
    plt.legend()
    plt.grid(True)
    plt.show()

# recommendation table
def generate_recommendation_table(df, cost_list):
    churn_probs = df.groupby("RiskScore")["ChurnFlag"].mean()
    avg_value = df.groupby("RiskScore")["MonthlyCharges"].mean()

    recommendations = []

    for cost in cost_list:
        ev = (churn_probs * avg_value) - cost

        positive_scores = ev[ev > 0].index.tolist()

        if len(positive_scores) == 0:
            threshold = "No profitable intervention"
        else:
            threshold = f"RiskScore ≥ {positive_scores[0]}"

        recommendations.append({
            "OfferCost": cost,
            "OptimalThreshold": threshold
        })

    rec_df = pd.DataFrame(recommendations)
    print("\nRecommendation Table")
    print(rec_df)

    #return rec_df

def main():
    # load and clean data
    df = pd.read_csv("data/telco_churn.csv")
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df.dropna(subset=["TotalCharges"], inplace=True)

    # convert churn from yes/no to 1/0
    df = convert_churn_to_numeric(df)

    # create buckets for churn probability by monthlycharges
    # low = 0-40, medium = 40-70, high = 70+
    churn_probability_by_charge_bucket(df)

    # assign risk scores
    df = assign_risk_score(df)

    # evaluate risk scores
    evaluate_risk_score(df)

    # ev at one cost 
    compute_expected_value(df, offer_cost=15)

    # cost sensitivity
    cost_list = [5,10,15,20,25]
    compute_cost_sensitivity(df, cost_list)
    plot_ev_by_risk(df, cost_list)
    generate_recommendation_table(df, cost_list)

if __name__ == "__main__":
    main()
