import streamlit as st
import json
import re
import random
import hashlib
import os
import time  # Import the time module for delays

# --- Constants ---
ACCOUNTS_FILE = 'accounts.json'
VERIFICATION_CODE_LENGTH = 6


# --- Data Persistence Functions ---

def load_accounts():
    """Loads account data from the JSON file."""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.warning(f"Warning: {ACCOUNTS_FILE} is corrupted or empty. Starting with no accounts.")
            return {}
    return {}


def save_accounts(accounts):
    """Saves account data to the JSON file."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)
    # st.success("Account data saved!") # This can be chatty, only show when necessary


# --- Email and Password Utilities ---

def generate_verification_code():
    """Generates a random numeric verification code."""
    return ''.join(random.choices('0123456789', k=VERIFICATION_CODE_LENGTH))


def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()


# --- Streamlit App Functions ---

def register_account_page():
    """Displays the account registration form."""
    st.subheader("Register New Account")

    with st.form("register_form"):
        username = st.text_input("Desired Username").strip()
        password = st.text_input("Password", type="password").strip()

        submitted = st.form_submit_button("Register")

        if submitted:
            accounts = st.session_state.accounts
            if username in accounts:
                st.error("Username already exists. Please choose a different one.")
                return
            if not username:
                st.error("Username cannot be empty.")
                return
            if len(password) < 6:
                st.error("Password must be at least 6 characters long.")
                return
            if not re.search(r"[a-z]", password):
                st.error("Password must contain at least one lowercase letter.")
                return
            if not re.search(r"[A-Z]", password):
                st.error("Password must contain at least one uppercase letter.")
                return
            if not re.search(r"\d", password):
                st.error("Password must contain at least one digit.")
                return
            if not re.search(r"[!@#$%^&*()_+={}\[\]|\\:;'<>,.?/`~-]", password):
                st.error("Password must contain at least one special character.")
                return

            # Simulate sending verification email (or directly create account for simplicity)
            # For this example, we will directly create the account without a real email verification
            hashed_password = hash_password(password)
            accounts[username] = {
                'password_hash': hashed_password,
                'my_list': []
            }
            st.session_state.accounts = accounts  # Update session state
            save_accounts(st.session_state.accounts)  # Save immediately
            st.success(f"Account '{username}' created successfully!")
            st.session_state.page = "login"  # Go to login page after successful registration
            st.rerun()  # Rerun to change page


def login_account_page():
    """Displays the login form."""
    st.subheader("Login to Account")

    with st.form("login_form"):
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password").strip()
        submitted = st.form_submit_button("Login")

        if submitted:
            accounts = st.session_state.accounts
            if username not in accounts:
                st.error("Invalid username or password.")
                return

            stored_password_hash = accounts[username]['password_hash']
            entered_password_hash = hash_password(password)

            if stored_password_hash == entered_password_hash:
                st.session_state.logged_in_user = username
                st.success(f"Welcome, {username}! You have successfully logged in.")
                st.session_state.page = "list_management"  # Change page to list management
                st.rerun()  # Rerun to change page
            else:
                st.error("Invalid username or password.")


def manage_user_list_page():
    """Allows a logged-in user to view and add items to their personal list."""
    username = st.session_state.logged_in_user
    st.subheader(f"{username}'s List Management")

    accounts = st.session_state.accounts
    user_data = accounts[username]
    my_list_current = user_data.get('my_list', [])  # Get the current list

    st.write("### Your Current List:")

    if my_list_current:
        st.write("Check an item to immediately remove it with an animation:")

        # We need a temporary list to build what will be the new my_list
        # This prevents modifying the list while iterating over it, which can cause issues.
        updated_list_after_removal = []
        item_removed_this_cycle = False  # Flag to know if any item was removed in this run

        # Iterate over a copy to safely check checkboxes
        for idx, item in enumerate(my_list_current):
            checkbox_key = f"remove_item_{idx}_{item}"

            # Check if the checkbox for this item is currently checked
            # If a checkbox is checked, this loop iteration will re-run.
            if st.checkbox(item, key=checkbox_key):
                # If the item is still in the original list (safety check)
                if item in user_data['my_list']:
                    # Display a temporary message for the "animation" effect
                    st.info(f"'{item}' is getting deleted...")
                    time.sleep(0.5)
                    st.info(f"DONE! '{item}' is deleted!")

                    time.sleep(0.5)  # Pause for half a second for the "animation"

                    user_data['my_list'].remove(item)  # Remove item from the actual list
                    st.session_state.accounts = accounts  # Update session state
                    save_accounts(st.session_state.accounts)  # Save changes to file
                    item_removed_this_cycle = True
                    st.rerun()  # Rerun immediately to show the list without the removed item
                    # The script execution stops here and restarts, so the item will be gone on the next render.
            else:
                # If the checkbox is not checked, keep the item in the list
                updated_list_after_removal.append(item)

        # If an item was just removed and we rerun, this part won't be reached in the same cycle.
        # It's here for completeness if a different removal strategy without immediate rerun was used.
        # However, with st.rerun() inside the loop, the list updates directly.

    else:
        st.info("Your list is empty. Add some items!")

    st.write("---")  # Separator

    new_item = st.text_input("Add New Item to List", key="add_new_item_input").strip()
    if st.button("Add Item", key="add_item_button"):
        if new_item:
            # Check against the current list in user_data
            if new_item in user_data['my_list']:
                st.warning(f"'{new_item}' is already in your list.")
            else:
                user_data['my_list'].append(new_item)
                st.session_state.accounts = accounts
                save_accounts(st.session_state.accounts)
                st.success(f"'{new_item}' added to your list!")
                st.rerun()
        else:
            st.warning("Item cannot be empty.")

    st.write('---')

    # Clear List functionality
    if st.button('Clear All Items', key="clear_list_button"):
        if user_data.get('my_list'):
            user_data['my_list'] = []
            st.session_state.accounts = accounts
            save_accounts(st.session_state.accounts)
            st.success("Your list has been cleared!")
            st.rerun()
        else:
            st.info("Your list is already empty.")

    st.write("---")  # Separator
    if st.button("Logout", key="logout_button"):
        del st.session_state.logged_in_user
        st.session_state.page = "home"
        st.rerun()


def main_app():
    """Main function to run the Streamlit account management system."""
    st.set_page_config(page_title="List-An-Item", layout="centered")
    st.title("Welcome to List-An-Item!")

    if 'accounts' not in st.session_state:
        st.session_state.accounts = load_accounts()
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'logged_in_user' not in st.session_state:
        st.session_state.logged_in_user = None

    if st.session_state.logged_in_user:
        st.sidebar.write(f"Logged in as: **{st.session_state.logged_in_user}**")
        manage_user_list_page()
    elif st.session_state.page == "home":
        st.write("Please Click The Arrow On the Top-Left Of Your Screen And Press An Action To Get Started!")
        if st.sidebar.button("Register New Account", key="home_register"):
            st.session_state.page = "register"
            st.rerun()
        if st.sidebar.button("Login", key="home_login"):
            st.session_state.page = "login"
            st.rerun()
    elif st.session_state.page == "register":
        register_account_page()
        if st.button("Back to Home", key="reg_back"):
            st.session_state.page = "home"
            st.rerun()
    elif st.session_state.page == "login":
        login_account_page()
        if st.button("Back to Home", key="login_back"):
            st.session_state.page = "home"
            st.rerun()
    else:
        st.session_state.page = "home"
        st.rerun()


main_app()
