# Copyright (c) 2024, Culinary Order Management and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def execute(filters=None):
	"""Generate role permissions and user assignment report"""
	
	# Get data first to determine if we need user columns
	# For role filter, we need to check if there are users
	data = get_data(filters)
	
	# Determine if we need user columns based on data
	# If data has user field filled, show user columns
	show_user_columns = False
	if filters and filters.get("user"):
		show_user_columns = True
	elif data and any(row.get("user") for row in data):
		show_user_columns = True
	
	# Adjust filters to include user column flag
	if filters:
		filters["_show_user_columns"] = show_user_columns
	
	columns = get_columns(filters)
	
	return columns, data


def get_columns(filters=None):
	"""Define report columns - show user columns only if user filter is set or role filter has users"""
	filters = filters or {}
	columns = []
	
	# Show user columns if explicitly requested (user filter or role filter with users)
	show_user_columns = filters.get("user") or filters.get("_show_user_columns", False)
	if show_user_columns:
		columns.extend([
			{
				"fieldname": "user",
				"label": _("User"),
				"fieldtype": "Link",
				"options": "User",
				"width": 150
			},
			{
				"fieldname": "user_name",
				"label": _("User Name"),
				"fieldtype": "Data",
				"width": 200
			},
		])
	
	# Always show role columns
	columns.extend([
		{
			"fieldname": "role",
			"label": _("Role"),
			"fieldtype": "Link",
			"options": "Role",
			"width": 180
		},
		{
			"fieldname": "doctype",
			"label": _("DocType"),
			"fieldtype": "Link",
			"options": "DocType",
			"width": 180
		},
	])
	
	# Permission checkboxes - full names
	columns.extend([
		{
			"fieldname": "read",
			"label": _("Read"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "write",
			"label": _("Write"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "create",
			"label": _("Create"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "delete",
			"label": _("Delete"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "submit",
			"label": _("Submit"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "cancel",
			"label": _("Cancel"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "export",
			"label": _("Export"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "print",
			"label": _("Print"),
			"fieldtype": "Check",
			"width": 80
		},
		{
			"fieldname": "email",
			"label": _("Email"),
			"fieldtype": "Check",
			"width": 80
		},
	])
	
	return columns


def get_filters():
	"""Define report filters - this is used by Frappe to show filter UI"""
	return [
		{
			"fieldname": "user",
			"label": _("User"),
			"fieldtype": "Link",
			"options": "User",
			"default": ""
		},
		{
			"fieldname": "role",
			"label": _("Role"),
			"fieldtype": "Link",
			"options": "Role",
			"default": ""
		},
		{
			"fieldname": "doctype",
			"label": _("DocType"),
			"fieldtype": "Link",
			"options": "DocType",
			"default": ""
		},
	]


def get_data(filters=None):
	"""Fetch data for the report"""
	filters = filters or {}
	data = []
	
	# Custom roles to report on
	custom_roles = [
		"Agreement Specialist",
		"Invoice Specialist", 
		"Portal Operations Specialist",
		"Payment Specialist",
		"Business Development Manager"
	]
	
	# Standard roles that have custom doctype permissions
	standard_roles_with_custom_perms = [
		"Sales Manager",
		"Sales User",
		"Accounts Manager",
		"Accounts User"
	]
	
	# DocTypes to include
	custom_doctypes = [
		"Agreement", "Proforma Invoice",
		"Lieferando Invoice", "Uber Eats Invoice", "Wolt Invoice",
		"WooCommerce Order", "WooCommerce Server",
		"Company Claim", "Stripe Transfers", "Payment Details", "Stripe Connect Account"
	]
	
	# Apply filters - ensure only one filter is active
	user_filter = filters.get("user") or ""
	role_filter = filters.get("role") or ""
	doctype_filter = filters.get("doctype") or ""
	
	# If multiple filters are set, prioritize: user > role > doctype
	active_filters = sum([1 for f in [user_filter, role_filter, doctype_filter] if f])
	if active_filters > 1:
		# Multiple filters detected - prioritize user > role > doctype
		if user_filter:
			role_filter = ""
			doctype_filter = ""
		elif role_filter:
			doctype_filter = ""
	
	# Scenario 1: User filter is set - show user's roles and permissions
	if user_filter:
		# Get user's roles
		user_roles = frappe.db.get_all(
			"Has Role",
			filters={"parent": user_filter},
			fields=["role"],
			pluck="role"
		)
		
		# Get user info
		user_info = frappe.db.get_value(
			"User",
			user_filter,
			["full_name", "email"],
			as_dict=True
		)
		user_name = user_info.full_name if user_info else user_filter
		if user_info and user_info.email:
			user_name = f"{user_name} ({user_info.email})"
		
		# Filter roles if role filter is set
		if role_filter:
			if role_filter in user_roles:
				roles_to_check = [role_filter]
			else:
				# User doesn't have this role
				return []
		else:
			# Only show roles that are in our custom/standard list
			all_relevant_roles = custom_roles + standard_roles_with_custom_perms
			roles_to_check = [r for r in user_roles if r in all_relevant_roles]
		
		# Filter doctypes
		if doctype_filter:
			doctypes_to_check = [doctype_filter] if frappe.db.exists("DocType", doctype_filter) else []
		else:
			doctypes_to_check = custom_doctypes
		
		# For each role the user has, show permissions
		for role in roles_to_check:
			for doctype in doctypes_to_check:
				if not frappe.db.exists("DocType", doctype):
					continue
				
				perm = _get_permission(doctype, role)
				if perm:
					data.append(_build_row(user_filter, user_name, role, doctype, perm))
	
	# Scenario 2: Role filter is set - show users with this role and their permissions
	elif role_filter:
		# Get all users with this role
		users_with_role = frappe.db.get_all(
			"Has Role",
			filters={"role": role_filter},
			fields=["parent"],
			pluck="parent"
		)
		
		# Filter doctypes
		if doctype_filter:
			doctypes_to_check = [doctype_filter] if frappe.db.exists("DocType", doctype_filter) else []
		else:
			doctypes_to_check = custom_doctypes
		
		# If users exist, show permissions for each user
		if users_with_role:
			for user in users_with_role:
				# Get user info
				user_info = frappe.db.get_value(
					"User",
					user,
					["full_name", "email"],
					as_dict=True
				)
				if not user_info:
					continue
					
				user_name = user_info.full_name if user_info else user
				if user_info.email:
					user_name = f"{user_name} ({user_info.email})"
				
				# Show permissions for this role
				for doctype in doctypes_to_check:
					if not frappe.db.exists("DocType", doctype):
						continue
					
					perm = _get_permission(doctype, role_filter)
					if perm:
						data.append(_build_row(user, user_name, role_filter, doctype, perm))
		else:
			# No users with this role - show role permissions anyway (without user columns)
			# User columns will not be shown because filters.get("user") is False
			for doctype in doctypes_to_check:
				if not frappe.db.exists("DocType", doctype):
					continue
				
				perm = _get_permission(doctype, role_filter)
				if perm:
					data.append(_build_row("", "", role_filter, doctype, perm))
	
	# Scenario 3: No user or role filter - show role-based permissions (no users)
	else:
		# Determine which roles to check
		roles_to_check = custom_roles + standard_roles_with_custom_perms
		
		# Determine which doctypes to check
		if doctype_filter:
			doctypes_to_check = [doctype_filter] if frappe.db.exists("DocType", doctype_filter) else []
		else:
			doctypes_to_check = custom_doctypes
		
		# Show permissions for each role-doctype combination
		for role in roles_to_check:
			if not frappe.db.exists("Role", role):
				continue
			
			for doctype in doctypes_to_check:
				if not frappe.db.exists("DocType", doctype):
					continue
				
				perm = _get_permission(doctype, role)
				if perm:
					# No user, so leave user fields empty
					data.append(_build_row("", "", role, doctype, perm))
	
	# Sort by user (empty last), then role, then doctype
	data.sort(key=lambda x: (
		x.get("user", "zzz"),  # Empty users go to end
		x.get("role", ""),
		x.get("doctype", "")
	))
	
	return data


def _get_permission(doctype, role):
	"""Get permission for a doctype and role"""
	# Try Custom DocPerm first
	perm = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
		["read", "write", "create", "delete", "submit", "cancel", "export", "print", "email"],
		as_dict=True
	)
	
	# If no custom permission, check standard DocType permissions
	if not perm:
		perm = frappe.db.get_value(
			"DocPerm",
			{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
			["read", "write", "create", "delete", "submit", "cancel", "export", "print", "email"],
			as_dict=True
		)
	
	return perm


def _build_row(user, user_name, role, doctype, perm):
	"""Build a data row"""
	return {
		"user": user,
		"user_name": user_name,
		"role": role,
		"doctype": doctype,
		"read": perm.get("read", 0),
		"write": perm.get("write", 0),
		"create": perm.get("create", 0),
		"delete": perm.get("delete", 0),
		"submit": perm.get("submit", 0),
		"cancel": perm.get("cancel", 0),
		"export": perm.get("export", 0),
		"print": perm.get("print", 0),
		"email": perm.get("email", 0),
	}
