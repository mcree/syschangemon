from syschangemon.core.dictdiff import DictDiff
from syschangemon.core.model import Session


class SessionDiff:

    def __init__(self, old_session: Session, new_session: Session):

        self.old_session = old_session
        self.new_session = new_session

        old_urls = set(old_session.all_urls())
        new_urls = set(new_session.all_urls())

        self.found_urls = new_urls - old_urls
        self.lost_urls = old_urls - new_urls
        self.equal_urls = old_urls & new_urls

        self.diffs = []
        for url in self.equal_urls:
            old_state = old_session.get_state(url)
            old_label = old_state['url']
            new_state = new_session.get_state(url)
            new_label = new_state['url']
            diff = DictDiff(old_state, old_label, new_state, new_label, ['id', 'sessionid', 'uuid'])
            if not diff.is_empty():
                self.diffs.append(diff)

    @property
    def is_empty(self):
        return len(self.diffs) == 0

    def __repr__(self):
        res = ""
        res += "- old session @ %s\n" % self.old_session['stamp']
        for url in self.lost_urls:
            res += "  " + url

        res += "+ new session @ %s\n" % self.new_session['stamp']
        for url in self.found_urls:
            res += "  " + url

        if self.is_empty():
            res += "= no difference"
        else:
            for diff in self.diffs:
                res += str(diff)

        return res
