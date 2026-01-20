from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
import traceback

def log_transaction_safe(secret_key, message_content="SMS Log"):
    """
    Attempts to log to Stellar. 
    Returns the Transaction Hash if successful.
    Returns None if it fails (so the app doesn't crash).
    """
    if not secret_key:
        return None

    try:
        # Use Testnet
        server = Server("https://horizon-testnet.stellar.org")
        source_keypair = Keypair.from_secret(secret_key)
        
        # Load account (Network call)
        source_account = server.load_account(account_id=source_keypair.public_key)

        # Build transaction (Send 1 XLM to self with a memo)
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
                base_fee=100
            )
            .append_payment_op(destination=source_keypair.public_key, asset=Asset.native(), amount="1")
            .add_text_memo("MedLink Log") # Simple text memo
            .set_timeout(30)
            .build()
        )

        # Submit
        transaction.sign(source_keypair)
        response = server.submit_transaction(transaction)
        print(f"Stellar Log Success: {response['hash']}")
        return response['hash']

    except Exception:
        # SAFETY NET: Just print error and continue. Do NOT raise exception.
        print("Stellar Log Skipped (Error ignored)")
        return None