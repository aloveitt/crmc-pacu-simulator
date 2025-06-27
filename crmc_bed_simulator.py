import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="CRMC PACU ROI Simulator", layout="wide")

# --- Password Protection ---
PASSWORD = "CRMC2024"
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("🔒 CRMC PACU ROI Simulator")
    pwd = st.text_input("Enter password to access:", type="password")
    if pwd == PASSWORD:
        st.session_state['authenticated'] = True
        st.experimental_rerun()
    else:
        st.stop()

# --- App Content Begins Here ---
if 'est_throughput_gain' not in st.session_state:
    st.session_state['est_throughput_gain'] = 0

tab1, tab2 = st.tabs(["📊 ROI Simulator", "💸 Cost Avoidance"])

with st.expander("ℹ️ Help & Definitions"):
    st.markdown("""
    ### Input Definitions

    **Surgeries per Week**: Include only those that recover in PACU.  
    **PACU Holds**: Patients held in PACU due to unavailable floor/med-surg beds.  
    **Throughput Gain**: Estimate of increased PACU efficiency by adding 6 extended stay beds.  

    **Transfers Accepted**: Additional transfers allowed due to freed inpatient capacity.  
    **ED Holds**: Time ED patients wait for an inpatient bed.  
    **OR Idle Time**: Lost minutes due to cases backing up into PACU.

    ### Calculation Summary

    - Additional cases = gain in PACU capacity × 52 weeks  
    - Revenue = added surgical + transfer revenue  
    - Cost avoidance = ED + OR idle  
    - Net Gain = cumulative revenue – staffing/capital cost
    """)

with tab1:
    st.title("CRMC Extended Stay Bed ROI Simulator")
    st.markdown("🔹 This simulation models the addition of **6 extended stay beds**.")

    st.sidebar.header("Surgical Case Assumptions")
    surgeries_per_week = st.sidebar.number_input("Surgeries per week", value=0)
    avg_pacu_time_min = st.sidebar.number_input("Avg PACU time per case (min)", value=0)
    pacu_bays = st.sidebar.number_input("PACU bays", value=0)
    pacu_holds_per_week = st.sidebar.number_input("PACU holds per week", value=0)
    revenue_per_case = st.sidebar.number_input("Revenue per surgical case ($)", value=0)

    st.sidebar.header("Staffing & Cost Assumptions")
    cost_to_add_beds = st.sidebar.number_input("Capital cost to add 6 beds ($)", value=0)
    new_ftes = st.sidebar.number_input("New FTEs needed", value=0)
    fte_cost_per_year = st.sidebar.number_input("Annual cost per FTE ($)", value=0)

    st.sidebar.header("Transfer Volume Impact")
    transfers_per_week = st.sidebar.number_input("Additional transfers accepted per week", value=0)
    revenue_per_transfer = st.sidebar.number_input("Revenue per transfer ($)", value=0)

    st.header("Throughput Gain Estimator")
    blocked_hours = st.number_input("PACU hours lost per week due to holds", value=0)
    bay_hours = st.number_input("Total PACU capacity hours/week", value=0)

    if bay_hours > 0:
        est_gain = (blocked_hours / bay_hours) * 100
        st.metric("Estimated Throughput Gain (%)", f"{est_gain:.1f}%")
        if st.button("Use this value in simulation"):
            st.session_state['est_throughput_gain'] = round(est_gain)
            st.success(f"Throughput gain set to {round(est_gain)}% in simulation.")
    else:
        st.warning("PACU capacity hours must be greater than zero.")

    throughput_gain_pct = st.slider("Override throughput gain (%) if known", 0, 100, st.session_state['est_throughput_gain'])

    avg_hours_per_week = 40 * 5
    pacu_throughput_per_bay = (60 / avg_pacu_time_min) * (avg_hours_per_week / 8) if avg_pacu_time_min > 0 else 0
    pacu_capacity = pacu_bays * pacu_throughput_per_bay
    new_capacity = pacu_capacity * (1 + throughput_gain_pct / 100)

    added_cases_per_week = max(0, new_capacity - pacu_capacity)
    added_cases_per_year = added_cases_per_week * 52
    transfer_cases_per_year = transfers_per_week * 52

    revenue_surgical = added_cases_per_year * revenue_per_case
    revenue_transfers = transfer_cases_per_year * revenue_per_transfer
    total_annual_revenue = revenue_surgical + revenue_transfers

    additional_operating_costs = new_ftes * fte_cost_per_year
    annual_net_revenue = total_annual_revenue - additional_operating_costs

    years = np.arange(0, 6)
    net_gain = np.zeros_like(years, dtype=float)
    for i in range(1, len(years)):
        net_gain[i] = net_gain[i-1] + annual_net_revenue
    net_gain -= cost_to_add_beds

    col1, col2, col3 = st.columns(3)
    col1.metric("Added surgical cases/week", f"{added_cases_per_week:.1f}")
    col2.metric("Annual surgical revenue", f"${revenue_surgical:,.0f}")
    col3.metric("Annual transfer revenue", f"${revenue_transfers:,.0f}")

    st.subheader("Cumulative Net Gain (Surgical + Transfer Revenue)")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(years, net_gain, marker='o', label='Cumulative Net Gain')
    ax.axhline(0, color='gray', linestyle='--')
    ax.set_xlabel('Years from Now')
    ax.set_ylabel('Cumulative Net Gain ($ after capital and staffing costs)')
    ax.set_title('Projected ROI from PACU Expansion')
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

with tab2:
    st.title("Cost Avoidance Estimator")
    st.subheader("ED Boarding Cost")
    ed_hours = st.number_input("ED boarding hours per week", value=0)
    ed_cost_per_hour = st.number_input("Cost per ED boarding hour ($)", value=0)
    ed_annual_cost = ed_hours * ed_cost_per_hour * 52

    st.subheader("OR Idle Time")
    or_idle_minutes = st.number_input("OR idle minutes/week due to PACU", value=0)
    or_idle_cost_per_min = st.number_input("Cost per idle OR minute ($)", value=0)
    or_annual_cost = or_idle_minutes * or_idle_cost_per_min * 52

    total_avoided_cost = ed_annual_cost + or_annual_cost
    st.metric("Cost Avoidance Total", f"${total_avoided_cost:,.0f}")
