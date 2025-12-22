// Copyright (c) 2024, Culinary Order Management and Contributors
// License: MIT. See LICENSE

frappe.query_reports["Role and Permissions Report"] = {
	"onload": function(report) {
		// Wait for filters to be ready
		setTimeout(() => {
			const user_filter = report.get_filter("user");
			const role_filter = report.get_filter("role");
			const doctype_filter = report.get_filter("doctype");
			
			if (user_filter) {
				const original_onchange = user_filter.df.onchange;
				user_filter.df.onchange = function() {
					const user_value = report.get_filter_value("user");
					if (user_value) {
						// Clear other filters
						if (role_filter && role_filter.get_value()) {
							role_filter.set_value("");
						}
						if (doctype_filter && doctype_filter.get_value()) {
							doctype_filter.set_value("");
						}
					}
					if (original_onchange) original_onchange.call(this);
				};
			}
			
			if (role_filter) {
				const original_onchange = role_filter.df.onchange;
				role_filter.df.onchange = function() {
					const role_value = report.get_filter_value("role");
					if (role_value) {
						// Clear other filters
						if (user_filter && user_filter.get_value()) {
							user_filter.set_value("");
						}
						if (doctype_filter && doctype_filter.get_value()) {
							doctype_filter.set_value("");
						}
					}
					if (original_onchange) original_onchange.call(this);
				};
			}
			
			if (doctype_filter) {
				const original_onchange = doctype_filter.df.onchange;
				doctype_filter.df.onchange = function() {
					const doctype_value = report.get_filter_value("doctype");
					if (doctype_value) {
						// Clear other filters
						if (user_filter && user_filter.get_value()) {
							user_filter.set_value("");
						}
						if (role_filter && role_filter.get_value()) {
							role_filter.set_value("");
						}
					}
					if (original_onchange) original_onchange.call(this);
				};
			}
		}, 100);
	},
	"filters": [
		{
			"fieldname": "user",
			"label": __("User"),
			"fieldtype": "Link",
			"options": "User"
		},
		{
			"fieldname": "role",
			"label": __("Role"),
			"fieldtype": "Link",
			"options": "Role"
		},
		{
			"fieldname": "doctype",
			"label": __("DocType"),
			"fieldtype": "Link",
			"options": "DocType"
		}
	]
};
