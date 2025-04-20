import streamlit as st
from .fund_management import render_fund_management
from .account_management import render_account_management
from .upload_panel import render_upload_panel
from .imported_files_panel import render_imported_files_panel
from .manual_entries_panel import render_manual_entries_panel
from .history_panel import render_history_panel


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