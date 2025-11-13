from django.dispatch import Signal

# Signal provides the instance that changed
business_changed = Signal()

userSignupSignal=Signal()
businessSignupSignal=Signal()
planSignal=Signal()
