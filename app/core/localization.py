from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_LOCALE_CODES = ("en", "es", "pt-BR")
DEFAULT_LOCALE_CODE = "en"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "brand": "Malipod",
        "nav.home": "Home",
        "nav.register": "Register",
        "nav.login": "Login",
        "nav.profile": "Profile",
        "nav.subscriptions": "Subscriptions",
        "nav.logout": "Logout",
        "language.label": "Language",
        "register.title": "Create your account",
        "register.subtitle": (
            "Create your Malipod account to sync your podcasts everywhere."
        ),
        "register.nickname": "Nickname",
        "register.email": "Email",
        "register.password": "Password",
        "register.confirm_password": "Confirm password",
        "register.picture_url": "Picture URL",
        "register.submit": "Create account",
        "register.login_link": "Already have an account? Sign in",
        "login.title": "Welcome back",
        "login.subtitle": "Sign in to continue your listening journey.",
        "login.identifier": "Email or nickname",
        "login.password": "Password",
        "login.submit": "Sign in",
        "login.register_link": "Need an account? Create one",
        "profile.title": "Your profile",
        "profile.subtitle": "Review your public identity and regional preferences.",
        "profile.nickname": "Nickname",
        "profile.email": "Email",
        "profile.language": "Preferred language",
        "profile.picture_url": "Picture URL",
        "profile.last_access": "Last access",
        "profile.created_at": "Created",
        "profile.updated_at": "Updated",
        "profile.save_language": "Update language",
        "profile.logout": "Log out",
        "profile.account_title": "Account",
        "profile.export_data": "Export data",
        "profile.import_data": "Import data",
        "profile.danger_zone": "Danger zone",
        "profile.danger_zone_description": (
            "Here, your data is yours, and you can do whatever you want with it."
        ),
        "profile.delete_data_title": "Delete data",
        "profile.delete_data_description": (
            "Removes all data except your account. Type "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> to confirm."
        ),
        "profile.delete_user_title": "Delete account",
        "profile.delete_user_description": (
            "Permanently removes your account and all data. Type "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> to confirm."
        ),
        "profile.confirm_placeholder": "DELETE",
        "profile.confirm_button": "Confirm",
        "errors.user_exists": "User already exists.",
        "errors.invalid_login": "Invalid login.",
        "errors.nickname": (
            "Nickname must use 8 to 16 letters, numbers, underscores, or hyphens."
        ),
        "errors.password_match": "Passwords must match.",
        "errors.password_length": "Password must contain at least 8 characters.",
        "errors.email": "Enter a valid email address.",
        "errors.picture_url": "Enter a valid picture URL.",
        "errors.language": "Choose a supported language.",
        "errors.profile_forbidden": "Profile not available.",
        "subscriptions.title": "Your subscriptions",
        "subscriptions.subtitle": "Browse, search, and manage the podcasts you follow.",
        "subscriptions.search": "Search",
        "subscriptions.search_placeholder": "Search podcasts",
        "subscriptions.sort": "Sort",
        "subscriptions.sort_recent": "Most recent",
        "subscriptions.sort_oldest": "Oldest",
        "subscriptions.view": "View",
        "subscriptions.view_list": "List",
        "subscriptions.view_grid": "Grid",
        "subscriptions.export_opml": "Export OPML",
        "subscriptions.add_title": "Add podcast",
        "subscriptions.add_placeholder": "Podcast feed URL (https://...)",
        "subscriptions.add_submit": "Add",
        "subscriptions.empty_title": "No subscriptions yet",
        "subscriptions.empty_description": (
            "Add a podcast feed URL to start syncing across your devices."
        ),
        "subscriptions.episodes_count": "Episodes",
        "subscriptions.last_episode": "Last episode",
        "subscriptions.last_episode_unknown": "Unknown",
        "subscriptions.add_success": (
            "Podcast submitted. Import will run in background."
        ),
        "subscriptions.add_invalid_url": "Enter a valid http or https feed URL.",
        "subscriptions.add_duplicate": "You already follow this podcast.",
        "podcast_detail.website": "Website",
        "podcast_detail.by_author": "by",
        "podcast_detail.episodes_title": "Episodes",
        "podcast_detail.empty_episodes_title": "No episodes yet",
        "podcast_detail.empty_episodes_description": (
            "Episodes will show up after the feed is imported."
        ),
        "podcast_detail.not_found_title": "Podcast not found",
        "podcast_detail.not_found_description": (
            "This podcast does not exist or is not available."
        ),
        "podcast_detail.back_to_subscriptions": "Back to subscriptions",
        "podcast_detail.sort_label": "Order",
        "podcast_detail.sort_recent": "Newest first",
        "podcast_detail.sort_oldest": "Oldest first",
        "home.hero_title_prefix": "Sync your podcasts",
        "home.hero_title_highlight": "on any app",
        "home.hero_description": (
            "Malipod is a self-hosted gpodder-compatible server to sync "
            "subscriptions, episodes, and progress across devices — "
            "with privacy and control."
        ),
        "home.card_sync_title": "Synchronization",
        "home.card_sync_description": (
            "Keep your podcast list and episodes aligned across all your devices."
        ),
        "home.card_api_title": "Compatible API",
        "home.card_api_description": (
            "Endpoints compatible with gpodder clients for automatic "
            "setup and local catalog."
        ),
        "home.logged_in_hint": (
            "You are already logged in. Use the top menu to access "
            "your profile or log out."
        ),
        "home.quickstart_title": "Get started in 2 minutes",
        "home.step1_title": "Create your account",
        "home.step1_description": "Register and set your nickname.",
        "home.step2_title": "Connect your app",
        "home.step2_description": (
            "Use your Malipod credentials in your gpodder-compatible client."
        ),
        "home.step3_title": "Sync",
        "home.step3_description": (
            "Subscriptions and progress will be available on all your devices."
        ),
        "home.api_docs": "Server documentation",
        "home.api_open": "Open",
        "home.unavailable_title": "Server temporarily unavailable",
        "home.unavailable_description": (
            "Some readiness checks failed. Try again shortly."
        ),
        "home.feature_privacy_title": "Privacy",
        "home.feature_privacy_description": (
            "Your data stays on your server. No tracking and no "
            "dependency on external services."
        ),
        "home.feature_control_title": "Control",
        "home.feature_control_description": (
            "Use Malipod as your sync foundation and evolve with "
            "features like lists and a local directory."
        ),
        "home.feature_multidevice_title": "Multi-device",
        "home.feature_multidevice_description": (
            "Phone, tablet, desktop — keep the experience consistent and synced."
        ),
    },
    "es": {
        "brand": "Malipod",
        "nav.home": "Inicio",
        "nav.register": "Registro",
        "nav.login": "Entrar",
        "nav.profile": "Perfil",
        "nav.subscriptions": "Suscripciones",
        "nav.logout": "Salir",
        "language.label": "Idioma",
        "register.title": "Crea tu cuenta",
        "register.subtitle": (
            "Crea tu cuenta de Malipod para sincronizar tus podcasts en todos "
            "tus dispositivos."
        ),
        "register.nickname": "Nickname",
        "register.email": "Correo electrónico",
        "register.password": "Contraseña",
        "register.confirm_password": "Confirmar contraseña",
        "register.picture_url": "URL de la imagen",
        "register.submit": "Crear cuenta",
        "register.login_link": "¿Ya tienes cuenta? Inicia sesión",
        "login.title": "Bienvenido de nuevo",
        "login.subtitle": "Inicia sesión para continuar tu experiencia de audio.",
        "login.identifier": "Correo o nickname",
        "login.password": "Contraseña",
        "login.submit": "Entrar",
        "login.register_link": "¿Necesitas una cuenta? Créala",
        "profile.title": "Tu perfil",
        "profile.subtitle": (
            "Revisa tu identidad pública y tus preferencias regionales."
        ),
        "profile.nickname": "Nickname",
        "profile.email": "Correo electrónico",
        "profile.language": "Idioma preferido",
        "profile.picture_url": "URL de la imagen",
        "profile.last_access": "Último acceso",
        "profile.created_at": "Creado",
        "profile.updated_at": "Actualizado",
        "profile.save_language": "Actualizar idioma",
        "profile.logout": "Cerrar sesión",
        "profile.account_title": "Cuenta",
        "profile.export_data": "Exportar datos",
        "profile.import_data": "Importar datos",
        "profile.danger_zone": "Zona de peligro",
        "profile.danger_zone_description": (
            "Aquí, tus datos son tuyos, y puedes hacer con ellos lo que quieras."
        ),
        "profile.delete_data_title": "Eliminar datos",
        "profile.delete_data_description": (
            "Elimina todos los datos excepto la cuenta. Escribe "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> para confirmar."
        ),
        "profile.delete_user_title": "Eliminar cuenta",
        "profile.delete_user_description": (
            "Elimina permanentemente la cuenta y todos los datos. Escribe "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> para confirmar."
        ),
        "profile.confirm_placeholder": "DELETE",
        "profile.confirm_button": "Confirmar",
        "errors.user_exists": "El usuario ya existe.",
        "errors.invalid_login": "Login inválido.",
        "errors.nickname": (
            "El nickname debe usar entre 8 y 16 letras, números, guiones bajos "
            "o guiones."
        ),
        "errors.password_match": "Las contraseñas deben coincidir.",
        "errors.password_length": "La contraseña debe tener al menos 8 caracteres.",
        "errors.email": "Ingresa un correo válido.",
        "errors.picture_url": "Ingresa una URL válida para la imagen.",
        "errors.language": "Elige un idioma soportado.",
        "errors.profile_forbidden": "Perfil no disponible.",
        "subscriptions.title": "Tus suscripciones",
        "subscriptions.subtitle": (
            "Explora, busca y administra los podcasts que sigues."
        ),
        "subscriptions.search": "Buscar",
        "subscriptions.search_placeholder": "Buscar podcasts",
        "subscriptions.sort": "Ordenar",
        "subscriptions.sort_recent": "Más recientes",
        "subscriptions.sort_oldest": "Más antiguos",
        "subscriptions.view": "Vista",
        "subscriptions.view_list": "Lista",
        "subscriptions.view_grid": "Cuadrícula",
        "subscriptions.export_opml": "Exportar OPML",
        "subscriptions.add_title": "Agregar podcast",
        "subscriptions.add_placeholder": "URL del feed (https://...)",
        "subscriptions.add_submit": "Agregar",
        "subscriptions.empty_title": "Aún no tienes suscripciones",
        "subscriptions.empty_description": (
            "Agrega una URL de feed para empezar a sincronizar en tus dispositivos."
        ),
        "subscriptions.episodes_count": "Episodios",
        "subscriptions.last_episode": "Último episodio",
        "subscriptions.last_episode_unknown": "Desconocido",
        "subscriptions.add_success": (
            "Podcast enviado. La importación correrá en segundo plano."
        ),
        "subscriptions.add_invalid_url": "Ingresa una URL http o https válida.",
        "subscriptions.add_duplicate": "Ya sigues este podcast.",
        "podcast_detail.website": "Sitio web",
        "podcast_detail.by_author": "por",
        "podcast_detail.episodes_title": "Episodios",
        "podcast_detail.empty_episodes_title": "Aún no hay episodios",
        "podcast_detail.empty_episodes_description": (
            "Los episodios aparecerán después de importar el feed."
        ),
        "podcast_detail.not_found_title": "Podcast no encontrado",
        "podcast_detail.not_found_description": (
            "Este podcast no existe o no está disponible."
        ),
        "podcast_detail.back_to_subscriptions": "Volver a suscripciones",
        "podcast_detail.sort_label": "Orden",
        "podcast_detail.sort_recent": "Más recientes",
        "podcast_detail.sort_oldest": "Más antiguos",
        "home.hero_title_prefix": "Sincroniza tus podcasts",
        "home.hero_title_highlight": "en cualquier app",
        "home.hero_description": (
            "Malipod es un servidor self-hosted compatible con gpodder "
            "para sincronizar suscripciones, episodios y progreso entre "
            "dispositivos — con privacidad y control."
        ),
        "home.card_sync_title": "Sincronización",
        "home.card_sync_description": (
            "Mantén tu lista de podcasts y episodios alineados en todos "
            "tus dispositivos."
        ),
        "home.card_api_title": "API compatible",
        "home.card_api_description": (
            "Endpoints compatibles con clientes gpodder para "
            "configuración automática y catálogo local."
        ),
        "home.logged_in_hint": (
            "Ya estás conectado. Usa el menú de arriba para acceder "
            "a tu perfil o cerrar sesión."
        ),
        "home.quickstart_title": "Empieza en 2 minutos",
        "home.step1_title": "Crea tu cuenta",
        "home.step1_description": "Regístrate y define tu nickname.",
        "home.step2_title": "Conecta tu app",
        "home.step2_description": (
            "Usa tus credenciales de Malipod en tu cliente compatible con gpodder."
        ),
        "home.step3_title": "Sincroniza",
        "home.step3_description": (
            "Suscripciones y progreso estarán disponibles en todos tus dispositivos."
        ),
        "home.api_docs": "Documentación del servidor",
        "home.api_open": "Abrir",
        "home.unavailable_title": "Servidor temporalmente no disponible",
        "home.unavailable_description": (
            "Algunas verificaciones de disponibilidad fallaron. "
            "Inténtalo de nuevo en unos instantes."
        ),
        "home.feature_privacy_title": "Privacidad",
        "home.feature_privacy_description": (
            "Tus datos se quedan en tu servidor. Sin rastreo y sin "
            "dependencia de servicios externos."
        ),
        "home.feature_control_title": "Control",
        "home.feature_control_description": (
            "Usa Malipod como base de sincronización y evoluciona con "
            "funciones como listas y directorio local."
        ),
        "home.feature_multidevice_title": "Multi-dispositivo",
        "home.feature_multidevice_description": (
            "Teléfono, tablet, escritorio — mantén la experiencia "
            "consistente y sincronizada."
        ),
    },
    "pt-BR": {
        "brand": "Malipod",
        "nav.home": "Início",
        "nav.register": "Cadastro",
        "nav.login": "Entrar",
        "nav.profile": "Perfil",
        "nav.subscriptions": "Subscrições",
        "nav.logout": "Sair",
        "language.label": "Idioma",
        "register.title": "Crie sua conta",
        "register.subtitle": (
            "Crie sua conta no Malipod para sincronizar seus podcasts em todos "
            "os seus dispositivos."
        ),
        "register.nickname": "Nickname",
        "register.email": "E-mail",
        "register.password": "Senha",
        "register.confirm_password": "Confirmar senha",
        "register.picture_url": "URL da foto",
        "register.submit": "Criar conta",
        "register.login_link": "Já tem conta? Faça login",
        "login.title": "Bem-vindo de volta",
        "login.subtitle": "Entre para continuar sua jornada sonora.",
        "login.identifier": "E-mail ou nickname",
        "login.password": "Senha",
        "login.submit": "Entrar",
        "login.register_link": "Precisa de uma conta? Crie uma",
        "profile.title": "Seu perfil",
        "profile.subtitle": (
            "Revise sua identidade pública e suas preferências regionais."
        ),
        "profile.nickname": "Nickname",
        "profile.email": "E-mail",
        "profile.language": "Idioma preferido",
        "profile.picture_url": "URL da foto",
        "profile.last_access": "Último acesso",
        "profile.created_at": "Criado em",
        "profile.updated_at": "Atualizado em",
        "profile.save_language": "Atualizar idioma",
        "profile.logout": "Sair",
        "profile.account_title": "Conta",
        "profile.export_data": "Exportar dados",
        "profile.import_data": "Importar dados",
        "profile.danger_zone": "Zona de perigo",
        "profile.danger_zone_description": (
            "Aqui, os seus dados são seus, e você pode fazer deles o que quiser."
        ),
        "profile.delete_data_title": "Deletar dados",
        "profile.delete_data_description": (
            "Remove todos os dados exceto a conta. Digite "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> para confirmar."
        ),
        "profile.delete_user_title": "Deletar usuário",
        "profile.delete_user_description": (
            "Remove permanentemente a conta e todos os dados. Digite "
            '<span class="font-mono bg-error/10 px-1 rounded">'
            "DELETE</span> para confirmar."
        ),
        "profile.confirm_placeholder": "DELETE",
        "profile.confirm_button": "Confirmar",
        "errors.user_exists": "Usuário já existe.",
        "errors.invalid_login": "Login inválido.",
        "errors.nickname": (
            "O nickname deve usar de 8 a 16 letras, números, sublinhados ou hífens."
        ),
        "errors.password_match": "As senhas precisam ser iguais.",
        "errors.password_length": "A senha precisa ter pelo menos 8 caracteres.",
        "errors.email": "Informe um e-mail válido.",
        "errors.picture_url": "Informe uma URL válida para a foto.",
        "errors.language": "Escolha um idioma suportado.",
        "errors.profile_forbidden": "Perfil indisponível.",
        "subscriptions.title": "Minhas subscrições",
        "subscriptions.subtitle": (
            "Veja, pesquise e gerencie os podcasts que você segue."
        ),
        "subscriptions.search": "Pesquisar",
        "subscriptions.search_placeholder": "Pesquisar podcasts",
        "subscriptions.sort": "Ordenar",
        "subscriptions.sort_recent": "Mais recentes",
        "subscriptions.sort_oldest": "Mais antigos",
        "subscriptions.view": "Visualização",
        "subscriptions.view_list": "Lista",
        "subscriptions.view_grid": "Grid",
        "subscriptions.export_opml": "Exportar OPML",
        "subscriptions.add_title": "Adicionar podcast",
        "subscriptions.add_placeholder": "URL do feed (https://...)",
        "subscriptions.add_submit": "Adicionar",
        "subscriptions.empty_title": "Você ainda não segue nenhum podcast",
        "subscriptions.empty_description": (
            "Adicione uma URL de feed para começar a sincronizar nos seus devices."
        ),
        "subscriptions.episodes_count": "Episódios",
        "subscriptions.last_episode": "Último episódio",
        "subscriptions.last_episode_unknown": "Desconhecido",
        "subscriptions.add_success": (
            "Podcast enviado. A importação vai rodar em background."
        ),
        "subscriptions.add_invalid_url": (
            "Informe uma URL de feed http ou https válida."
        ),
        "subscriptions.add_duplicate": "Você já segue esse podcast.",
        "podcast_detail.website": "Website",
        "podcast_detail.by_author": "por",
        "podcast_detail.episodes_title": "Episódios",
        "podcast_detail.empty_episodes_title": "Nenhum episódio ainda",
        "podcast_detail.empty_episodes_description": (
            "Os episódios vão aparecer depois que o feed for importado."
        ),
        "podcast_detail.not_found_title": "Podcast não encontrado",
        "podcast_detail.not_found_description": (
            "Esse podcast não existe ou não está disponível."
        ),
        "podcast_detail.back_to_subscriptions": "Voltar para subscrições",
        "podcast_detail.sort_label": "Ordenar",
        "podcast_detail.sort_recent": "Mais recentes",
        "podcast_detail.sort_oldest": "Mais antigos",
        "home.hero_title_prefix": "Sincronize seus podcasts",
        "home.hero_title_highlight": "em qualquer app",
        "home.hero_description": (
            "O Malipod é um servidor self-hosted compatível com gpodder "
            "para sincronizar assinaturas, episódios e progresso entre "
            "dispositivos — com privacidade e controle."
        ),
        "home.card_sync_title": "Sincronização",
        "home.card_sync_description": (
            "Mantenha sua lista de podcasts e seus episódios alinhados "
            "em todos os seus dispositivos."
        ),
        "home.card_api_title": "API compatível",
        "home.card_api_description": (
            "Endpoints compatíveis com clientes gpodder para "
            "configuração automática e catálogo local."
        ),
        "home.logged_in_hint": (
            "Você já está logado. Use o menu no topo para acessar seu perfil ou sair."
        ),
        "home.quickstart_title": "Comece em 2 minutos",
        "home.step1_title": "Crie sua conta",
        "home.step1_description": "Cadastre-se e defina seu nickname.",
        "home.step2_title": "Conecte no seu app",
        "home.step2_description": (
            "Use as credenciais do Malipod no seu cliente compatível com gpodder."
        ),
        "home.step3_title": "Sincronize",
        "home.step3_description": (
            "Assinaturas e progresso ficam disponíveis em todos os dispositivos."
        ),
        "home.api_docs": "Documentação do servidor",
        "home.api_open": "Abrir",
        "home.unavailable_title": "Servidor temporariamente indisponível",
        "home.unavailable_description": (
            "Alguns checks de prontidão falharam. Tente novamente em instantes."
        ),
        "home.feature_privacy_title": "Privacidade",
        "home.feature_privacy_description": (
            "Seus dados ficam no seu servidor. Sem rastreamento e "
            "sem dependência de serviços externos."
        ),
        "home.feature_control_title": "Controle",
        "home.feature_control_description": (
            "Use o Malipod como base para sincronização e evolua com "
            "recursos como listas e diretório local."
        ),
        "home.feature_multidevice_title": "Multi-dispositivo",
        "home.feature_multidevice_description": (
            "Telefone, tablet, desktop — mantenha a experiência "
            "consistente e sincronizada."
        ),
    },
}


@dataclass(frozen=True)
class LocaleResolution:
    requested_locale: str | None
    effective_locale: str
    source: str
    is_supported: bool


def normalize_locale(locale: str | None) -> str | None:
    if locale is None:
        return None
    normalized = locale.strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if lowered == "pt-br":
        return "pt-BR"
    if lowered in {"en", "es"}:
        return lowered
    return None


def is_supported_locale(locale: str | None) -> bool:
    return normalize_locale(locale) in SUPPORTED_LOCALE_CODES


def get_translation_catalog(locale: str) -> dict[str, str]:
    normalized = normalize_locale(locale) or DEFAULT_LOCALE_CODE
    return TRANSLATIONS.get(normalized, TRANSLATIONS[DEFAULT_LOCALE_CODE])
