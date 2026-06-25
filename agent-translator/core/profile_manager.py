import os
import shutil
import sys

def get_profiles_dir():
    return os.path.join(os.path.dirname(__file__), "..", "prompts", "profiles")

def list_profiles():
    base_dir = get_profiles_dir()
    if not os.path.exists(base_dir):
        print("Profiles directory not found.")
        return []
    
    profiles = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith("-deleted-")]
    return sorted(profiles)

def create_profile():
    print("\n--- Create New Profile ---")
    name = input("Enter profile name: ").strip()
    if not name:
        print("Profile name cannot be empty.")
        return
        
    base_dir = get_profiles_dir()
    profile_path = os.path.join(base_dir, name)
    default_path = os.path.join(base_dir, "default")
    
    if os.path.exists(profile_path):
        print(f"Profile '{name}' already exists!")
        return
        
    os.makedirs(profile_path)
    print(f"Created directory: {profile_path}")
    
    rules_content = """# Profile Rules / Skill Instructions
Buraya bu profile özel mimari kuralları, proje detaylarını veya LLM'in takınmasını istediğiniz "Skill" (Yetenek) davranışlarını yazın.
Örnek: "Sen bir Prompt Optimize edicisin. Çeviriyi yapmadan önce kullanıcıya kullanılacak frameworkleri ve veritabanı tercihlerini sormak için `unclear` dizisini kullan."
"""
    with open(os.path.join(profile_path, "rules.md"), "w") as f:
        f.write(rules_content)

    print(f"\n[SUCCESS] Profile '{name}' created successfully!")

    # Print instructional message
    abs_path = os.path.abspath(profile_path)
    print("\n" + "="*40)
    print("ACTION REQUIRED:")
    print("Your new profile is located at:")
    print(f" -> {abs_path}")
    print("\nPlease open the rules.md file in your editor and add your custom skills/rules:")
    print(" - rules.md : Add your domain-specific rules or LLM skills here.")
    print("              (The base system and JSON compiler will automatically load from default)")
    print("="*40 + "\n")

def delete_profile():
    print("\n--- Delete Profile ---")
    profiles = list_profiles()
    if not profiles:
        print("No profiles available.")
        return
        
    for i, p in enumerate(profiles, 1):
        print(f"{i}. {p}")
        
    choice = input("Select profile to delete (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(profiles):
        print("Cancelled.")
        return
        
    target = profiles[int(choice) - 1]
    if target == "default":
        print("Cannot delete the 'default' profile!")
        return
        
    confirm = input(f"Are you sure you want to delete profile '{target}'? (y/n): ").strip().lower()
    if confirm == "y":
        target_path = os.path.join(get_profiles_dir(), target)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        deleted_name = f"-deleted-{timestamp}-{target}"
        deleted_path = os.path.join(get_profiles_dir(), deleted_name)
        os.rename(target_path, deleted_path)
        print(f"Profile '{target}' soft-deleted as '{deleted_name}'.")
    else:
        print("Cancelled.")

def manage():
    try:
        import readline
    except ImportError:
        pass
        
    while True:
        print("\n=== PROMPT PROFILES MANAGER ===")
        print("1. List Profiles")
        print("2. Create New Profile")
        print("3. Delete Profile")
        print("4. Exit")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            print("\n--- Available Profiles ---")
            for p in list_profiles():
                print(f" - {p}")
        elif choice == "2":
            create_profile()
        elif choice == "3":
            delete_profile()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    manage()
