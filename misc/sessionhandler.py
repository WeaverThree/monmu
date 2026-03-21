from django.conf import settings

import evennia
from evennia.server.sessionhandler import ServerSessionHandler
from evennia.server.portal import amp
from evennia.server.signals import (
    SIGNAL_ACCOUNT_POST_FIRST_LOGIN,
    SIGNAL_ACCOUNT_POST_LAST_LOGOUT,
    SIGNAL_ACCOUNT_POST_LOGIN,
    SIGNAL_ACCOUNT_POST_LOGOUT,
)

_MULTISESSION_MODE = settings.MULTISESSION_MODE


class MonServerSessionHandler(ServerSessionHandler):
    # We're here to prevent the server from leaking IPs all over. Should only need to override a little for that.

    def login(self, session, account, force=False, testmode=False):
        """
        Log in the previously unloggedin session and the account we by now should know is connected
        to it. After this point we assume the session to be logged in one way or another.

        Args:
            session (Session): The Session to authenticate.
            account (Account): The Account identified as associated with this Session.
            force (bool): Login also if the session thinks it's already logged in
                (this can happen for auto-authenticating protocols)
            testmode (bool, optional): This is used by unittesting for
                faking login without any AMP being actually active.

        """
        if session.logged_in and not force:
            # don't log in a session that is already logged in.
            return

        account.is_connected = True

        # sets up and assigns all properties on the session
        session.at_login(account)

        # account init
        account.at_init()

        # Check if this is the first time the *account* logs in
        if account.db.FIRST_LOGIN:
            account.at_first_login()
            del account.db.FIRST_LOGIN

        account.at_pre_login()

        if _MULTISESSION_MODE == 0:
            # disconnect all previous sessions.
            self.disconnect_duplicate_sessions(session)

        nsess = len(self.sessions_from_account(account))
        # string = "Logged in: {account} {address} ({nsessions} session(s) total)"
        # string = string.format(account=account, address=session.address, nsessions=nsess)
        # session.log(string)
        session.logged_in = True
        # sync the portal to the session
        if not testmode:
            evennia.EVENNIA_SERVER_SERVICE.amp_protocol.send_AdminServer2Portal(
                session, operation=amp.SLOGIN, sessiondata={"logged_in": True, "uid": session.uid}
            )
        account.at_post_login(session=session)
        if nsess < 2:
            SIGNAL_ACCOUNT_POST_FIRST_LOGIN.send(sender=account, session=session)
        SIGNAL_ACCOUNT_POST_LOGIN.send(sender=account, session=session)

    def disconnect(self, session, reason="", sync_portal=True):
        """
        Called from server side to remove session and inform portal
        of this fact.

        Args:
            session (Session): The Session to disconnect.
            reason (str, optional): A motivation for the disconnect.
            sync_portal (bool, optional): Sync the disconnect to
                Portal side. This should be done unless this was
                called by self.portal_disconnect().

        """
        session = self.get(session.sessid)
        if not session:
            return

        if hasattr(session, "account") and session.account:
            # only log accounts logging off
            nsess = len(self.sessions_from_account(session.account)) - 1
            # sreason = " ({})".format(reason) if reason else ""
            # string = "Logged out: {account} {address} ({nsessions} sessions(s) remaining){reason}"
            # string = string.format(
            #     reason=sreason, account=session.account, address=session.address, nsessions=nsess
            # )
            # session.log(string)

            if nsess == 0:
                SIGNAL_ACCOUNT_POST_LAST_LOGOUT.send(sender=session.account, session=session)

        session.at_disconnect(reason)
        SIGNAL_ACCOUNT_POST_LOGOUT.send(sender=session.account, session=session)
        sessid = session.sessid
        if sessid in self and not hasattr(self, "_disconnect_all"):
            del self[sessid]
        if sync_portal:
            # inform portal that session should be closed.
            evennia.EVENNIA_SERVER_SERVICE.amp_protocol.send_AdminServer2Portal(
                session, operation=amp.SDISCONN, reason=reason
            )