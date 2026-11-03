import os

from auction.database import Base, engine, SessionLocal
from auction import models
from auction.security import hash_password

ADMIN_NAME = os.getenv("ADMIN_NAME", "admin").lower()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@test.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin12345")  

CUSTOMER_PERMS = ["product:list", "bid:create", "bid:list_own"]
OWNER_PERMS = [
    "product:list", "product:create", "product:update", "product:delete",
    "product:import", "bid:list_own", "bid:list_product", "bid:accept",
]
ADMIN_PERMS = sorted(set(CUSTOMER_PERMS + OWNER_PERMS +
                     ["user:manage", "role:manage"]))

ROLE_PERMISSIONS = {
    "admin": ADMIN_PERMS,
    "owner": OWNER_PERMS,
    "customer": CUSTOMER_PERMS,
}


def get_or_create_permission(db, code):
    perm = db.query(models.Permission).filter(
        models.Permission.code == code).first()
    if perm is None:
        perm = models.Permission(code=code)
        db.add(perm)
        db.flush()
    return perm


def get_or_create_role(db, name):
    role = db.query(models.Role).filter(models.Role.name == name).first()
    if role is None:
        role = models.Role(name=name)
        db.add(role)
        db.flush()
    return role


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1) الأدوار والصلاحيات
        for role_name, codes in ROLE_PERMISSIONS.items():
            role = get_or_create_role(db, role_name)
            existing = {p.code for p in role.permissions}
            for code in codes:
                if code not in existing:
                    role.permissions.append(get_or_create_permission(db, code))

        # 2) حساب الأدمن
        admin_role = get_or_create_role(db, "admin")
        admin = db.query(models.User).filter(
            models.User.name == ADMIN_NAME).first()
        if admin is None:
            db.add(models.User(
                name=ADMIN_NAME,
                email=ADMIN_EMAIL,
                password=hash_password(ADMIN_PASSWORD),
                role_id=admin_role.id,
            ))
            print(f"Admin created: {ADMIN_NAME}")
        else:
            print("Admin already exists")

        db.commit()
        print("Seeding done")
    finally:
        db.close()


if __name__ == "__main__":
    run()
