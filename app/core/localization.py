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
        "errors.user_exists": "user already exists",
        "errors.invalid_login": "login inválido",
        "errors.nickname": (
            "Nickname must use 8 to 16 letters, numbers, underscores, or hyphens."
        ),
        "errors.password_match": "Passwords must match.",
        "errors.email": "Enter a valid email address.",
        "errors.picture_url": "Enter a valid picture URL.",
        "errors.language": "Choose a supported language.",
        "errors.profile_forbidden": "Profile not available.",
    },
    "es": {
        "brand": "Malipod",
        "nav.home": "Inicio",
        "nav.register": "Registro",
        "nav.login": "Entrar",
        "nav.profile": "Perfil",
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
        "errors.user_exists": "user already exists",
        "errors.invalid_login": "login inválido",
        "errors.nickname": (
            "El nickname debe usar entre 8 y 16 letras, números, guiones bajos "
            "o guiones."
        ),
        "errors.password_match": "Las contraseñas deben coincidir.",
        "errors.email": "Ingresa un correo válido.",
        "errors.picture_url": "Ingresa una URL válida para la imagen.",
        "errors.language": "Elige un idioma soportado.",
        "errors.profile_forbidden": "Perfil no disponible.",
    },
    "pt-BR": {
        "brand": "Malipod",
        "nav.home": "Início",
        "nav.register": "Cadastro",
        "nav.login": "Entrar",
        "nav.profile": "Perfil",
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
        "errors.user_exists": "user already exists",
        "errors.invalid_login": "login inválido",
        "errors.nickname": (
            "O nickname deve usar de 8 a 16 letras, números, sublinhados ou hífens."
        ),
        "errors.password_match": "As senhas precisam ser iguais.",
        "errors.email": "Informe um e-mail válido.",
        "errors.picture_url": "Informe uma URL válida para a foto.",
        "errors.language": "Escolha um idioma suportado.",
        "errors.profile_forbidden": "Perfil indisponível.",
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
