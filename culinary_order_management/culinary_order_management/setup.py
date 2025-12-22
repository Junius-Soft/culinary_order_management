import frappe
from frappe.permissions import setup_custom_perms


def ensure_admin_company_permissions_clear(*args, **kwargs):
    """Ensure Administrator has no Company-level User Permission that hides cross-company docs.

    Called on after_install and after_migrate to avoid list visibility issues in dev/test.
    Safe no-op if records do not exist.
    """
    try:
        names = frappe.get_all(
            "User Permission",
            filters={"user": "Administrator", "allow": "Company"},
            pluck="name",
        )
        for name in names:
            try:
                frappe.delete_doc("User Permission", name, force=True)
            except Exception:
                # ignore if already deleted or protected
                pass
        if names:
            frappe.db.commit()
    except Exception:
        # defensive: do not block installs/migrations
        pass


def setup_custom_roles_and_permissions():
    """Setup custom roles and permissions for Culinary Order Management app.
    
    This function creates custom roles and sets up DEFAULT permissions for custom doctypes.
    IMPORTANT: Only creates permissions if they don't exist. Once created, permissions
    can be modified via UI (Permission Manager) and those changes will be preserved.
    
    Called only on after_install (first installation).
    NOT called on after_migrate to preserve manual changes made via UI.
    """
    try:
        from frappe.core.doctype.doctype.doctype import validate_permissions_for_doctype
        
        # Custom Doctypes that need permission configuration
        custom_doctypes = [
            "Agreement", "Proforma Invoice",
            "Lieferando Invoice", "Uber Eats Invoice", "Wolt Invoice",
            "WooCommerce Order", "WooCommerce Server",
            "Company Claim", "Stripe Transfers", "Payment Details", "Stripe Connect Account"
        ]
        
        # Role-based permissions configuration
        # Format: {doctype: {role: {permission: value}}}
        # Permissions: read, write, create, delete, submit, cancel, export, print, email
        role_permissions = {
            "Agreement": {
                "Sales Manager": {
                    "read": 1, "write": 1, "create": 1, "delete": 1, 
                    "submit": 1, "cancel": 1, "export": 1, "print": 1, "email": 1
                },
                "Agreement Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 1
                },
                "Sales User": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
                "Business Development Manager": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            "Proforma Invoice": {
                "Sales Manager": {
                    "read": 1, "write": 1, "create": 1, "delete": 1,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 1
                },
                "Sales User": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            # Invoice Specialist - Platform faturaları
            "Lieferando Invoice": {
                "Invoice Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            "Uber Eats Invoice": {
                "Invoice Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            "Wolt Invoice": {
                "Invoice Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            # Portal Operations Specialist - WooCommerce
            "WooCommerce Order": {
                "Portal Operations Specialist": {
                    "read": 1, "write": 1, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
                "Sales Manager": {
                    "read": 1, "write": 1, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
                "Sales User": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            "WooCommerce Server": {
                "Portal Operations Specialist": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 0, "email": 0
                },
            },
            # Payment Specialist - Payment işlemleri
            "Company Claim": {
                "Payment Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
                "Accounts Manager": {
                    "read": 1, "write": 1, "create": 1, "delete": 1,
                    "submit": 1, "cancel": 1, "export": 1, "print": 1, "email": 1
                },
            },
            "Stripe Transfers": {
                "Payment Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
                "Accounts Manager": {
                    "read": 1, "write": 1, "create": 1, "delete": 1,
                    "submit": 1, "cancel": 1, "export": 1, "print": 1, "email": 1
                },
            },
            "Payment Details": {
                "Payment Specialist": {
                    "read": 1, "write": 1, "create": 1, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 1, "email": 0
                },
            },
            "Stripe Connect Account": {
                "Payment Specialist": {
                    "read": 1, "write": 0, "create": 0, "delete": 0,
                    "submit": 0, "cancel": 0, "export": 1, "print": 0, "email": 0
                },
            },
        }
        
        for doctype in custom_doctypes:
            if not frappe.db.exists("DocType", doctype):
                continue
                
            # Setup custom permissions (copy from standard permissions)
            setup_custom_perms(doctype)
            
            # Add role-based permissions
            if doctype in role_permissions:
                for role, permissions in role_permissions[doctype].items():
                    if not frappe.db.exists("Role", role):
                        continue
                    
                    # Check if Custom DocPerm exists for this role (duplicate kontrolü ile)
                    existing_perms = frappe.db.get_all(
                        "Custom DocPerm",
                        filters={"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
                        fields=["name"]
                    )
                    
                    # Duplicate kayıtları temizle (birden fazla varsa)
                    if len(existing_perms) > 1:
                        # En son oluşturulanı tut, diğerlerini sil
                        perm_names = [p.name for p in existing_perms]
                        # En son oluşturulanı bul (creation tarihine göre)
                        latest_perm = frappe.db.get_value(
                            "Custom DocPerm",
                            {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
                            "name",
                            order_by="creation desc"
                        )
                        # Diğerlerini sil
                        for perm_name in perm_names:
                            if perm_name != latest_perm:
                                try:
                                    frappe.delete_doc("Custom DocPerm", perm_name, force=True, ignore_permissions=True)
                                except Exception:
                                    pass  # Ignore if already deleted
                        frappe.db.commit()
                        custom_docperm_name = latest_perm
                    elif len(existing_perms) == 1:
                        custom_docperm_name = existing_perms[0].name
                    else:
                        custom_docperm_name = None
                    
                    if not custom_docperm_name:
                        # Create new Custom DocPerm directly (without saving parent DocType)
                        # This avoids DocType validation issues
                        custom_docperm = frappe.get_doc({
                            "doctype": "Custom DocPerm",
                            "parent": doctype,
                            "parenttype": "DocType",
                            "parentfield": "permissions",
                            "role": role,
                            "permlevel": 0,
                            "if_owner": 0,
                        })
                        
                        # Set all permissions
                        for perm_name, perm_value in permissions.items():
                            setattr(custom_docperm, perm_name, perm_value)
                        
                        custom_docperm.flags.ignore_permissions = True
                        custom_docperm.flags.ignore_validate = True
                        custom_docperm.insert(ignore_permissions=True)
                    
                    # If Custom DocPerm already exists, skip - let users manage via UI
                    # This preserves any manual changes made in Permission Manager
                    
                    frappe.db.commit()
        
        # Validate permissions for each doctype
        for doctype in custom_doctypes:
            if frappe.db.exists("DocType", doctype):
                try:
                    validate_permissions_for_doctype(doctype)
                except Exception:
                    pass  # Ignore validation errors
        
        frappe.db.commit()
        
    except Exception as e:
        # Log error but don't block installation
        frappe.log_error(
            f"Error setting up custom roles and permissions: {str(e)}",
            "Setup Custom Roles and Permissions"
        )


