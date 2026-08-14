# Running the test suite

The project uses Django's built-in test runner (no pytest dependency) with
Oscar's test factories. Tests live in each app's `tests.py` and share fixtures
from `oasis/testutils.py`.

## Run everything

```bash
python manage.py test membership returns vendor messaging qa ratings recommendations apps.search oasis.tests
```

On Windows, prefix with `PYTHONIOENCODING=utf-8` so console output doesn't choke
on non-ASCII characters:

```bash
PYTHONIOENCODING=utf-8 python manage.py test <labels>
```

## Run one app

```bash
python manage.py test membership          # membership + member discount
python manage.py test returns             # returns / refunds / restock
python manage.py test apps.search         # search relevance
```

## What's covered (47 tests)

| App | Covers |
|-----|--------|
| `membership` | active/expired/cancelled state, member vs non-member discount via the custom offer condition, join/cancel views |
| `returns` | return-window eligibility, ownership, per-line returnable qty, create → approve → refund → restock, manager permissions |
| `vendor` | seller-rating aggregate + positive %, leave-feedback flow, can't-rate-unrelated-seller |
| `messaging` | thread creation, unread tracking, read-on-open, reply, outsider 403, can't-message-own-store |
| `qa` | ask/answer, seller-answer badge + ordering, anonymous blocked |
| `ratings` | star rendering (full/half/empty), score histogram, verified-purchase detection |
| `recommendations` | best-sellers ranking, buy-again from order history |
| `apps.search` | relevance ranking (title first), multi-word AND, any-term fallback |
| `oasis` | wishlist toggle, order tracking/invoice access control, coupon application |

## Notes

- The test runner auto-swaps the whitenoise manifest static storage for plain
  storage (see the `"test" in sys.argv` block in `settings.py`), so tests don't
  require `collectstatic`.
- Fixtures use `oasis.testutils` (`make_user`, `make_product`,
  `make_seller_product`, `place_order`) built on `oscar.test.factories`.
