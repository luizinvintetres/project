import streamlit as st
from .admin_panel.fund_management import render_fund_management
from .admin_panel.account_management import render_account_management
from .admin_panel.upload_panel import render_upload_panel
from .admin_panel.imported_files_panel import render_imported_files_panel
from .admin_panel.manual_entries_panel import render_manual_entries_panel
from .admin_panel.render_history_panel import render_history_panel


def render():
    st.header("⚙️ Administração")
    user_email = st.session_state.user.email

    render_fund_management(user_email)
    st.divider()

    render_account_management(user_email)
    st.divider()

    render_upload_panel(user_email)
    st.divider()

    render_imported_files_panel(user_email)
    st.divider()

    render_manual_entries_panel(user_email)
    st.divider()

    render_history_panel(user_email)
    