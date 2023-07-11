import secrets
import random


def random_email(nbytes: int = 10, domain: str = "@email.com"):
    return secrets.token_hex(nbytes=nbytes) + domain


def random_email_list() -> str:
    email_ls = [random_email() for _ in range(random.randint(1, 11))]

    # add random empty emails to list
    for _ in range(random.randint(1, 11)):
        email_ls.append(random.choice(("", " ", "  ")))

    random.shuffle(email_ls)

    sep = random.choice((",", ", ", ";", "; "))

    return sep.join(email_ls)
