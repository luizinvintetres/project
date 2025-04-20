import streamlit as st
from services.supabase_client import supabase, delete_file_records

def render_imported_files_panel(user_email: str) -> None:
    st.subheader("🧾 Meus Arquivos importados")
    logs = supabase.from_("import_log").select("filename").eq("uploader_email", user_email).execute().data or []
    if not logs:
        st.info("Você ainda não importou nenhum arquivo.")
        return
    filenames = sorted({r["filename"] for r in logs if r.get("filename")})
    for f in filenames:
        col1, col2 = st.columns([6,1])
        col1.write(f)
        if col2.button("❌", key=f"admin_del_{f}"):
            delete_file_records(filename=f, uploader_email=user_email)
            st.success(f"Registros do arquivo '{f}' foram apagados.")
            return