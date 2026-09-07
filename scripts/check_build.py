import sys

def test_startup():
    print("Verifying ARM-1 application startup...")
    try:
        import main
        print("SUCCESS: main.py imported cleanly!")
    except Exception as e:
        print(f"FAILURE: Application startup failed with error:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    test_startup()
