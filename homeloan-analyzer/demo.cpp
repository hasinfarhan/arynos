#include <bits/stdc++.h>

using namespace std;

// market
double property_base_val = 1000000;
double property_rent = property_base_val / (12 * 20); // rent_to_buy = 18y
double property_upside_rate = 0.08;
double opportunity_upside_rate = 0.15;
double loan_aprc = 0.075;
double property_tax = 0.005;
double maintenance_rate = 0.01;

// decision
double downpay_ratio;
double loan_term;
double investment_period_yr;
double min_acceptable_roi = 5;
double max_downpayment = 500000;
double max_monthly_pay = 6000;

void calc() {
    double loan = property_base_val * (1.0 - downpay_ratio);
    double mortgage_rounds = loan_term * 12;
    double monthly_aprc = loan_aprc / 12;
    double interest_compound = pow(1 + monthly_aprc, mortgage_rounds);
    double monthly_overhead_rate = (property_tax + maintenance_rate) / 12;
    double mortgage = loan * monthly_aprc * (interest_compound / (interest_compound - 1));
    
    double total_months = investment_period_yr * 12;
    double mortgage_paid = mortgage * total_months;
    double down_payment = property_base_val * downpay_ratio;
    double overall_paid = down_payment + mortgage_paid;

    if (down_payment > max_downpayment) return;
    if (!(max_monthly_pay >= mortgage && mortgage >= property_rent)) return;

    double equity = downpay_ratio + investment_period_yr / loan_term;
    double sold_value = equity * property_base_val * pow(1 + property_upside_rate, investment_period_yr) + property_base_val * monthly_overhead_rate;

    double monthly_opportunity_upside_rate = opportunity_upside_rate / 12;
    double monthly_saving = mortgage - property_rent;
    double monthly_opportunity_compound = pow(1 + monthly_opportunity_upside_rate, mortgage_rounds);
    double opportunity_compound = pow(1 + opportunity_upside_rate, investment_period_yr);
    double opportunity_value = down_payment * opportunity_compound + monthly_saving * (monthly_opportunity_compound - 1) / monthly_opportunity_upside_rate; 

    double gain = sold_value - opportunity_value;
    double monthly_gain = gain / total_months;
    double roi = (gain / overall_paid) * 100;

    if (roi < min_acceptable_roi) return;

    cout << "investment_period_yr: " << investment_period_yr << endl;
    cout << "loan_term: " << loan_term << endl;
    cout << "downpay_ratio: " << downpay_ratio << endl;
    cout << "down_payment: " << down_payment << endl;
    cout << "mortgage: " << mortgage << endl;
    cout << "property_rent: " << property_rent << endl;
    cout << "overall_paid: " << overall_paid << endl;
    cout << "monthly_gain: " << monthly_gain << endl;
    cout << "roi: " << roi << endl;
    cout << "....................." << endl;
}

int main() {
    for (int yr = 1; yr <= 10; yr++) {
        investment_period_yr = (double) yr;
        for (int tr = 15; tr <= 35; tr += 5) {
            loan_term = (double) tr;
            for (int rt = 5; rt <= 100; rt++) {
                downpay_ratio = (rt * 1.0) / 100.0;
                calc();
            }
        }
    }

    return 0;
}