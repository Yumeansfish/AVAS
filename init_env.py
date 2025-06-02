from pathlib import Path

def prompt(label: str) -> str:
    val = input(f"{label}: ").strip()
    return val

def main():
    print("Initializing .env file. Enter values or press Enter to leave blank.\n")

    aws_key     = prompt("AWS_ACCESS_KEY_ID")
    aws_secret  = prompt("AWS_SECRET_ACCESS_KEY")
    aws_region  = prompt("AWS_REGION")
    s3_bucket   = prompt("S3_BUCKET_NAME")

    sheet_id    = prompt("SHEET_ID")

    recipient   = prompt("RECIPIENT_EMAIL")
    smtp_server = prompt("SMTP_SERVER")
    smtp_port   = prompt("SMTP_PORT")
    smtp_user   = prompt("SMTP_USERNAME")
    smtp_pass   = prompt("SMTP_PASSWORD")
    from_email  = prompt("FROM_EMAIL")

    lines = [
        f"AWS_ACCESS_KEY_ID={aws_key}",
        f"AWS_SECRET_ACCESS_KEY={aws_secret}",
        f"AWS_REGION={aws_region}",
        f"S3_BUCKET_NAME={s3_bucket}",
        "",
        f"SHEET_ID={sheet_id}",
        "",
        f"RECIPIENT_EMAIL={recipient}",
        f"SMTP_SERVER={smtp_server}",
        f"SMTP_PORT={smtp_port}",
        f"SMTP_USERNAME={smtp_user}",
        f"SMTP_PASSWORD={smtp_pass}",
        f"FROM_EMAIL={from_email}"
    ]

    env_path = Path(__file__).parent / "core" / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    print(f".env file created at {env_path.resolve()}")

if __name__ == "__main__":
    main()

