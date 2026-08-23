from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Always return True so new users logging in via GitHub or Google 
        are directly registered and logged in without stopping at 3rdparty/signup.
        """
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # Ensure a username is populated from GitHub/Google profile data
        if not user.username:
            username = data.get('username') or data.get('nickname') or data.get('name')
            if username:
                user.username = username.replace(' ', '_').lower()
            else:
                provider = sociallogin.account.provider
                uid = sociallogin.account.uid
                user.username = f"{provider}_{uid}"[:30]
        return user
