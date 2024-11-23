# users.py: Foydalanuvchilar bilan bog'liq operatsiyalar
from .database import  Database
from datetime import datetime

class UserDatabase(Database):
    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL,
            username VARCHAR(255)  NULL,
            referrer_id INTEGER NULL,
            balance DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
            last_active DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES Users (id) ON DELETE SET NULL
        );
        """
        self.execute(sql, commit=True)

    def add_user(self, telegram_id: int, username: str, referrer_id=None, created_at=None):
        sql = """
        INSERT INTO Users(telegram_id, username, referrer_id, balance, created_at) VALUES(?, ?, ?, 0.0, ?)
        """
        if created_at is None:
            created_at = datetime.now().isoformat()
        self.execute(sql, parameters=(telegram_id, username, referrer_id, created_at), commit=True)

    def select_all_users(self):
        sql = """
        SELECT * FROM Users
        """
        return self.execute(sql, fetchall=True)

    def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, kwargs)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM Users;", fetchone=True)

    def delete_users(self):
        self.execute("DELETE FROM Users WHERE TRUE", commit=True)

    def update_user_balance(self, user_id: int, amount: float):
        sql = """
        UPDATE Users
        SET balance = balance + ?
        WHERE id = ?
        """
        self.execute(sql, parameters=(amount, user_id), commit=True)

    def update_user_last_active(self, user_id: int):
        sql = """
        UPDATE Users
        SET last_active = ?
        WHERE id = ?
        """
        last_active = datetime.now().isoformat()
        self.execute(sql, parameters=(last_active, user_id), commit=True)

    def create_table_referral_rewards(self):
        sql = """
        CREATE TABLE IF NOT EXISTS ReferralRewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            reward_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
            referrals_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE
        );
        """
        self.execute(sql, commit=True)

    def create_table_transaction_history(self):
        sql = """
        CREATE TABLE IF NOT EXISTS TransactionHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL, -- 'reward', 'withdraw'
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (id)
        );
        """
        self.execute(sql, commit=True)

    def update_referral_reward(self, referrer_id: int, reward_amount: float):
        sql_check = "SELECT * FROM ReferralRewards WHERE user_id = ?"
        reward = self.execute(sql_check, parameters=(referrer_id,), fetchone=True)

        if reward:
            sql_update = """
            UPDATE ReferralRewards 
            SET reward_amount = reward_amount + ?, referrals_count = referrals_count + 1
            WHERE user_id = ?
            """
            self.execute(sql_update, parameters=(reward_amount, referrer_id), commit=True)
        else:
            sql_insert = """
            INSERT INTO ReferralRewards(user_id, reward_amount, referrals_count) VALUES(?, ?, 1)
            """
            self.execute(sql_insert, parameters=(referrer_id, reward_amount), commit=True)


        # Update user balance
        self.update_user_balance(referrer_id, reward_amount)
        # Add transaction history
        self.add_transaction_history(referrer_id, reward_amount, 'reward')


    def withdraw_user_balance(self, user_id: int, amount: float):
        user = self.select_user(id=user_id)
        if user and user[4] >= amount:  # assuming balance is the 5th element
            sql = """
            UPDATE Users
            SET balance = balance - ?
            WHERE id = ?
            """
            self.execute(sql, parameters=(amount, user_id), commit=True)
            self.add_transaction_history(user_id, -amount, 'withdraw')
        else:
            print("Insufficient balance.")

    def add_transaction_history(self, user_id: int, amount: float, transaction_type: str):
        sql = """
        INSERT INTO TransactionHistory(user_id, amount, transaction_type, created_at)
        VALUES (?, ?, ?, ?)
        """
        created_at = datetime.now().isoformat()
        self.execute(sql, parameters=(user_id, amount, transaction_type, created_at), commit=True)

    def get_user_referral_summary(self, user_id: int):
        sql = """
        SELECT reward_amount, referrals_count
        FROM ReferralRewards
        WHERE user_id = ?
        """
        return self.execute(sql, parameters=(user_id,), fetchone=True)

    def get_user_referral_details(self, user_id: int):
        sql = """
        SELECT Users.username, Users.balance, ReferralRewards.reward_amount, ReferralRewards.referrals_count
        FROM Users
        LEFT JOIN ReferralRewards ON Users.id = ReferralRewards.user_id
        WHERE Users.id = ?
        """
        return self.execute(sql, parameters=(user_id,), fetchone=True)

    def count_users_added_since(self, since_time):
        sql = """
        SELECT COUNT(*) FROM Users WHERE created_at >= ?
        """
        return self.execute(sql, parameters=(since_time.isoformat(),), fetchone=True)[0]

    def count_active_users_since(self, since_time):
        sql = """
        SELECT COUNT(*) FROM Users WHERE last_active >= ?
        """
        return self.execute(sql, parameters=(since_time.isoformat(),), fetchone=True)[0]

    def check_if_admin(self, user_id: int) -> bool:
        sql = "SELECT 1 FROM Admins WHERE user_id = ?"
        result = self.execute(sql, parameters=(user_id,), fetchone=True)
        return result is not None
