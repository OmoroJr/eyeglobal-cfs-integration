app_name = "cfs_integration"
whitelisted_methods = ["cfs_integration.api.push_invoice","cfs_integration.api.receive_job"]
doc_events = {
    "Sales Invoice": {"on_submit": "cfs_integration.cfs_operations.rebates.create_rebate_for_invoice"},
    "Delivery Note": {"on_submit": "cfs_integration.cfs_operations.rebates.create_rebate_for_delivery"}
}
scheduler_events = {"monthly": ["cfs_integration.cfs_operations.rebates.generate_monthly_payouts"]}
