import argparse
import getpass
import sys

from sqlmodel import Session, SQLModel, select

from app.core.config import get_settings
from app.core.security import hash_password, utc_now
from app.db.models import Role, User
from app.db.session import create_db_engine


class AdminAlreadyExistsError(RuntimeError):
    pass


def create_admin(*, username: str, password: str, force: bool = False) -> User:
    engine = create_db_engine(get_settings().db_path)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.role == Role.admin)).first()
        if existing is not None and not force:
            raise AdminAlreadyExistsError
        now = utc_now()
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=Role.admin,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p_create = sub.add_parser("create-admin")
    p_create.add_argument("--username", help="Nombre de usuario del administrador")
    p_create.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "create-admin":
        username = args.username or input("Nombre de usuario: ").strip()
        password = getpass.getpass("Contraseña: ")
        try:
            create_admin(username=username, password=password, force=args.force)
        except AdminAlreadyExistsError:
            print(
                "Error: ya existe una cuenta de administrador. Use --force.", file=sys.stderr
            )
            return 1
        print("Administrador creado correctamente.")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
