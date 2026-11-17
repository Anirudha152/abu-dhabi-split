"""Abu Dhabi trip ledger. Single source of truth for the site: run to verify and write ../data.json.

Every expense is allocated in INR to people; every rupee paid in is recorded as a payment.
Checks: each expense's shares sum to its total; total spent == total paid; card spend reconciles."""
import json, os
from collections import defaultdict

PEOPLE = ['ani', 'baid', 'bhatnagar', 'nitye', 'mansi', 'gaurish', 'kavya', 'sanket', 'sumit', 'nehal', 'arnav', 'anushree']
NAMES = {p: p.capitalize() for p in PEOPLE}
NAMES.update(bhatnagar='L Bhatnagar', baid='L Baid')

# ---------------- Rates ----------------
TOPUPS = [(150, 4290), (2122, 55098), (1600, 41641), (1600, 41641)]   # (AED, INR)
WITHDRAW_AED, WITHDRAW_INR = 212.82, 5250
CARD_SPENT_AED = 5259.18
CARD_RATE = (sum(i for _, i in TOPUPS) - WITHDRAW_INR) / CARD_SPENT_AED  # 26.1295
DEFAULT_RATE = 26.15   # Nitye cash, Gaurish karting, anything without a stated rate
BAID_RATE = 26.36      # all of Baid's AED payments

ANI_LOADED = 3 * 40000 + 4290
BHATNAGAR_LOADED = sum(i for _, i in TOPUPS) - ANI_LOADED

expenses, payments = [], []
problems = []

def eq(*ps): return {p: 1 for p in ps}

def add(date, title, source, payer, aed, rate, shares, inr=None, notes=None, items=None):
    """shares: {person: weight} split pro rata on the total, or {person: aed_amount} when weights_are_aed."""
    total_inr = inr if inr is not None else aed * rate
    w = sum(shares.values())
    alloc = [{'person': p, 'aed': (aed * v / w) if aed is not None else None, 'inr': total_inr * v / w,
              'note': (notes or {}).get(p, '')} for p, v in shares.items()]
    for a in alloc:
        assert a['person'] in PEOPLE, (title, a['person'])
    expenses.append({'id': len(expenses) + 1, 'date': date, 'title': title, 'source': source, 'payer': payer,
                     'aed': aed, 'rate': rate, 'inr': total_inr, 'shares': alloc, 'items': items or []})

def itemised(date, title, source, payer, total_aed, rate, lines, discount_to=None):
    """lines: (item name, gross AED, 'a,b,c'). Optional pro-rata discount so lines sum to total_aed."""
    gross = sum(a for _, a, _ in lines)
    f = total_aed / gross
    if abs(gross - total_aed) > 0.005 and discount_to is None:
        problems.append(f'{title}: items {gross} != total {total_aed}')
    per, notes = defaultdict(float), defaultdict(list)
    for name, a, who in lines:
        ws = who.split(',')
        for p in ws:
            per[p] += a * f / len(ws)
        label = name if len(ws) == 1 else f'{name} (1/{len(ws)})'
        for p in ws:
            notes[p].append(label)
    items = [{'name': n, 'aed': round(a * f, 2), 'who': [w for w in who.split(',')]} for n, a, who in lines]
    def tidy(labels):  # '2× Item' instead of repeating identical lines
        counts = {}
        for l in labels: counts[l] = counts.get(l, 0) + 1
        return ', '.join(f'{n}× {l}' if n > 1 else l for l, n in counts.items())
    add(date, title, source, payer, total_aed, rate, dict(per), notes={p: tidy(v) for p, v in notes.items()}, items=items)
    return gross

CARD = 'Forex card'

# ---------------- Forex card (rate = net INR / AED spent) ----------------
add('2026-11-13', 'Khalidya Branch', CARD, 'card', 3.24, CARD_RATE, eq('ani'))
add('2026-11-13', "McDonald's (ADNOC)", CARD, 'card', 34, CARD_RATE, {'nitye': 11, 'ani': 23})
add('2026-11-13', "McDonald's (ADNOC)", CARD, 'card', 24, CARD_RATE, eq('bhatnagar'))
for _ in range(3):
    add('2026-11-13', 'Coffee, Jackson Trading', CARD, 'card', 2, CARD_RATE, eq('ani'))
add('2026-11-14', 'Five Guys', CARD, 'card', 73, CARD_RATE, eq('ani'))
add('2026-11-14', 'Pizza Hut, The Galleria', CARD, 'card', 59.8, CARD_RATE, eq('kavya', 'bhatnagar'))
add('2026-11-14', 'Taxi (Hazrat Bilal)', CARD, 'card', 98.7, CARD_RATE, eq('ani', 'kavya', 'bhatnagar', 'sumit'))
add('2026-11-14', 'Taxi, Arabia Taxi Abu Dhabi', CARD, 'card', 270, CARD_RATE, eq('ani', 'kavya', 'baid', 'mansi', 'gaurish'))
add('2026-11-14', 'Emaar, Burj Khalifa', CARD, 'card', 1095, CARD_RATE, eq('ani', 'kavya', 'baid', 'mansi', 'gaurish'))
add('2026-11-14', 'At The Top', CARD, 'card', 25, CARD_RATE, eq('ani'))
add('2026-11-14', 'At The Top', CARD, 'card', 137, CARD_RATE, eq('kavya'))
add('2026-11-14', 'At The Top', CARD, 'card', 57, CARD_RATE, eq('gaurish'))
rosas = itemised('2026-11-14', "Rosa's Thai, Dubai Mall", CARD, 'card', 668, CARD_RATE, [
    ('Thai Fried Chicken Wings, plate 1', 37, 'mansi'),
    ('Thai Fried Chicken Wings, half plate', 18.5, 'sumit'),
    ('Thai Fried Chicken Wings, half plate', 18.5, 'gaurish'),
    ('Milky Thai Bubble Tea', 27, 'ani'),
    ('Passionfruit & Strawberry Bubble Tea', 27, 'baid'),
    ("Rosa's Homemade Spring Rolls", 35, 'ani,nehal'),
    ('Pad Thai Veg & Tofu + extra fried egg', 66, 'ani'),
    ('Chilli & Basil Pad Kra Prow Veg & Tofu', 59, 'nehal,baid'),
    ('Green Curry Prawn', 68, 'mansi'),
    ('Green Curry Sliced Chicken', 67, 'kavya,sanket'),
    ('Hainanese-Style Chicken Rice', 53, 'kavya,sanket'),
    ('Drunken Noodle Minced Chicken', 66, 'sumit'),
    ('Drunken Noodle Prawn', 67, 'gaurish'),
    ('Green Curry Veg & Tofu', 59, 'nehal,baid'),
])
aj = itemised('2026-11-15', 'Al Jaber Gallery', CARD, 'card', 1219, CARD_RATE, [
    ('Asst Chocolate Dates Rual', 29, 'mansi'), ('Asst Chocolate Dates Rual', 29, 'mansi'),
    ('Asst Chocolate Dates Rual', 29, 'kavya'), ('Asst Chocolate Dates Rual', 29, 'kavya'),
    ('Asst Chocolate Dates Rual', 29, 'sanket'), ('Asst Chocolate Dates Rual', 29, 'sanket'),
    ('I Love Dubai Choco Dates', 55, 'mansi'), ('Lattafa Badee Al Oud Noble', 169, 'mansi'),
    ('Jomara Organic Dates Pistachio', 32, 'mansi'), ('Jomara Organic Dates', 35, 'ani'),
    ('Jomara Organic Dates', 35, 'mansi'),
    ("Al Mealim Deli Arabic (gift for Shilpi ma'am)", 55, 'ani,mansi,kavya,gaurish,baid'),
    ('Hazelnut Kunafa Chocolate', 55, 'ani'), ('Hazelnut Kunafa Chocolate', 55, 'kavya'),
    ('Hazelnut Kunafa Chocolate', 55, 'sanket'), ('ILD Milk Pistachio Kunafa', 55, 'ani'),
    ('ILD Milk Pistachio Kunafa', 55, 'sanket'), ('ILD Milk Pistachio Kunafa', 55, 'kavya'),
    ('MC Dub USB Lighter', 95, 'ani'), ('Camel Milk Pistachio Kunafa', 35, 'kavya'),
    ('Al Mealim Lux Arabic Sweets', 13, 'sanket'), ('Al Mealim Lux Arabic Sweets', 13, 'sanket'),
    ('ILD Sugar Free Dark Pistachio', 35, 'sanket'), ('SP Lighter w/ USB', 60, 'sanket'),
    ('ILD Milk Pistachio Kunafa (35)', 35, 'gaurish'), ('ILD Milk Pistachio Kunafa (35)', 35, 'gaurish'),
    ('ILD Milk Pistachio Kunafa (35)', 35, 'gaurish'), ('GP Bracelet', 25, 'gaurish'),
    ('GP Bracelet', 25, 'gaurish'), ('ER Earrings', 39, 'gaurish'), ('Lighter Stone', 29, 'kavya'),
], discount_to=1219)
add('2026-11-15', 'Taxi to Global Street', CARD, 'card', 97.5, CARD_RATE, eq('ani', 'nitye', 'nehal', 'sumit', 'sanket', 'baid'))
add('2026-11-15', 'Perfume, Thouq Al Hawameer', CARD, 'card', 350, CARD_RATE, {'ani': 225, 'nitye': 125})
add('2026-11-15', 'Perfume, Thouq Al Hawameer', CARD, 'card', 200, CARD_RATE, eq('sanket'))
add('2026-11-15', 'Taxi to the beach', CARD, 'card', 67, CARD_RATE, eq('ani', 'mansi', 'gaurish', 'baid', 'sumit', 'nehal'))
add('2026-11-15', 'Taxi back from Dubai', CARD, 'card', 279.5, CARD_RATE, eq('ani', 'mansi', 'anushree', 'nitye', 'sanket', 'arnav'))
add('2026-11-15', 'Taxi to Yas circuit (Tawasul)', CARD, 'card', 15, CARD_RATE, eq('ani', 'mansi', 'nitye'))
add('2026-11-15', 'Perfume, Al Majed for Oud', CARD, 'card', 115, CARD_RATE, eq('nitye'))
add('2026-11-15', 'Five Guys', CARD, 'card', 98, CARD_RATE, {'ani': 73, 'nitye': 25})
cf = itemised('2026-11-15', 'Carrefour, Yas Mall', CARD, 'card', 220.44, CARD_RATE, [
    ('Saray Arabic Sweet', 19.99, 'nitye'), ('Saray Arabic Sweet', 19.99, 'nitye'),
    ('Saray Arabic Sweet', 19.99, 'ani'), ('Saray Arabic Sweet', 19.99, 'mansi'),
    ('Dates w/ Nuts Premium', 29.39, 'mansi'),
    ('Khat Fard Pouch', 7.29, 'nitye'), ('Khat Fard Pouch', 7.29, 'nitye'),
    ('Khat Fard Pouch', 7.29, 'nitye'), ('Khat Fard Pouch', 7.29, 'nitye'),
    ('Mido Wafer Rolls', 7.49, 'nitye'), ('Mido Wafer Rolls', 7.49, 'nitye'),
    ('Mido Wafer Rolls', 7.49, 'ani'), ('Mido Wafer Rolls', 7.49, 'ani'), ('Mido Wafer Rolls', 7.49, 'mansi'),
    ('Kuche 100g', 15, 'nitye'), ('Kuche 100g', 15, 'mansi'),
    ('Plastic bag', 0.5, 'ani'), ('Plastic bag', 0.5, 'nitye'), ('Plastic bag', 0.5, 'mansi'),
    ('RJ Magnet', 6.49, 'nitye'), ('RJ Magnet', 6.49, 'mansi'),
])
add('2026-11-15', 'Taxi to campus (Platinum)', CARD, 'card', 47, CARD_RATE, eq('ani', 'mansi', 'nitye'))

# ---------------- Nitye's cash (AED @ 26.15) ----------------
NC = 'Nitye, cash'
add('2026-11-15', 'Global Street entry', NC, 'nitye', 180, DEFAULT_RATE, eq('ani', 'nitye', 'baid', 'sanket', 'sumit', 'nehal'))
add(None, 'Books 157 + dinner 100', NC, 'nitye', 257, DEFAULT_RATE, eq('bhatnagar'))
add(None, 'Cash for Mansi', NC, 'nitye', 70, DEFAULT_RATE, eq('mansi'))
add(None, 'Cash for Gaurish', NC, 'nitye', 50, DEFAULT_RATE, eq('gaurish'))
add(None, 'Cash for Kavya', NC, 'nitye', 50, DEFAULT_RATE, eq('kavya'))
add(None, 'Taxi', NC, 'nitye', 90, DEFAULT_RATE, eq('ani', 'sumit'))
add(None, 'Taxi', NC, 'nitye', 90, DEFAULT_RATE, eq('nitye', 'bhatnagar'))
dtf = itemised('2026-11-14', 'Din Tai Fung, Galleria', NC, 'nitye', 328, DEFAULT_RATE, [
    ('Nitye’s share', 60, 'nitye'), ('L Baid’s share', 52, 'baid'), ('L Bhatnagar’s share', 54, 'bhatnagar'),
    ('Mansi’s share', 54, 'mansi'), ('Gaurish’s share', 54, 'gaurish'), ('Kavya’s share', 54, 'kavya')])

# ---------------- Paid directly by individuals ----------------
add(None, 'Warner Bros. World', 'L Bhatnagar, card', 'bhatnagar', None, None,
    eq('ani', 'kavya', 'mansi', 'baid', 'bhatnagar', 'nitye', 'gaurish'), inr=57666)
add('2026-11-15', 'Taxi, Global Street to Dubai beach', 'Sanket, card', 'sanket', 70, 1838 / 70,
    eq('sanket', 'bhatnagar', 'nitye', 'arnav', 'anushree', 'kavya'), inr=1838)
add('2026-11-15', 'Go-karting, Yas', 'Gaurish', 'gaurish', 980, DEFAULT_RATE,
    eq('ani', 'nitye', 'mansi', 'gaurish', 'bhatnagar', 'baid', 'kavya'))
BS = 'L Baid'
add(None, 'Mosque', BS, 'baid', 30, BAID_RATE, eq('sanket', 'nehal', 'baid'))
add('2026-11-14', 'Taxi to Din Tai Fung', BS, 'baid', 78, BAID_RATE, eq('nitye', 'mansi', 'bhatnagar', 'baid', 'kavya', 'gaurish'))
add(None, 'Taxi, AD Mall to hostel', BS, 'baid', 67, BAID_RATE, eq('nitye', 'gaurish', 'baid'))
add('2026-11-15', 'Taxi back from Dubai', 'L Baid, card', 'baid', 286, 7540 / 286,
    eq('bhatnagar', 'kavya', 'gaurish', 'baid', 'nehal', 'sumit'), inr=7540)
add('2026-11-15', 'Chips at go-karting', BS, 'baid', 10, BAID_RATE, eq('kavya'))
add(None, 'Lebanese Roaster chocolates', BS, 'baid', 298, BAID_RATE, {'bhatnagar': 193, 'baid': 105})
add('2026-11-16', 'Taxi from Delhi airport', 'Ani, cash', 'ani', None, None, eq('ani', 'bhatnagar', 'nitye'), inr=605)

# ---------------- Payments in ----------------
def pay(person, inr, title, kind, date=None, expense=None):
    payments.append({'person': person, 'inr': inr, 'title': title, 'kind': kind, 'date': date, 'expense': expense})
pay('ani', ANI_LOADED, 'Loaded the forex card (3 × ₹40,000 + ₹4,290)', 'card', '2026-11-12')
pay('ani', -WITHDRAW_INR, f'Got back the forex card leftover ({WITHDRAW_AED} AED)', 'card')
pay('bhatnagar', BHATNAGAR_LOADED, 'Loaded the forex card (rest of the top-ups)', 'card', '2026-11-12')
for e in expenses:
    if e['payer'] != 'card':
        pay(e['payer'], e['inr'], e['title'], 'expense', e['date'], e['id'])
TRANSFERS = [('kavya', 'bhatnagar', 9000), ('mansi', 'bhatnagar', 9000), ('baid', 'bhatnagar', 9000), ('gaurish', 'bhatnagar', 8200)]
for frm, to, amt in TRANSFERS:
    pay(frm, amt, f'Cash to {NAMES[to]}', 'transfer')
    pay(to, -amt, f'Cash from {NAMES[frm]}', 'transfer')

# ---------------- Checks ----------------
ok = True
def check(label, got, want, tol=0.005):
    global ok
    good = abs(got - want) <= tol
    ok &= good
    print(f"  [{'OK ' if good else 'FAIL'}] {label}: {got:,.2f} vs {want:,.2f}")

print(f'Card rate {CARD_RATE:.4f}')
check("Rosa's items", rosas, 668)
check('Al Jaber gross less 140 discount', aj - 140, 1219)
check('Carrefour items', cf, 220.44)
check('Din Tai Fung split', dtf, 328)
for e in expenses:
    s = sum(a['inr'] for a in e['shares'])
    if abs(s - e['inr']) > 0.005:
        check(f"#{e['id']} {e['title']} shares", s, e['inr'])
card_aed = sum(e['aed'] for e in expenses if e['payer'] == 'card')
check('card spends = statement', card_aed, CARD_SPENT_AED)
check('card spent + withdrawn = loaded AED', card_aed + WITHDRAW_AED, sum(a for a, _ in TOPUPS))
check('card INR spread = net INR', sum(e['inr'] for e in expenses if e['payer'] == 'card'), sum(i for _, i in TOPUPS) - WITHDRAW_INR)
check('Ani + Bhatnagar loads', ANI_LOADED + BHATNAGAR_LOADED, sum(i for _, i in TOPUPS))
for msg in problems:
    ok = False; print('  [FAIL]', msg)

spent, paid = defaultdict(float), defaultdict(float)
for e in expenses:
    for a in e['shares']: spent[a['person']] += a['inr']
for p in payments: paid[p['person']] += p['inr']
check('total spent == total paid', sum(spent.values()), sum(paid.values()))
net = {p: paid[p] - spent[p] for p in PEOPLE}

# ---------------- Settle up: whole rupees, fewest payments ----------------
rounded = {p: round(net[p]) for p in PEOPLE}
drift = sum(rounded.values())
if drift:  # push the rounding rupee(s) onto the biggest creditor
    top = max(PEOPLE, key=lambda p: rounded[p]); rounded[top] -= drift
# Plan chosen so everyone who owes a small amount pays exactly one person; only the three
# largest debtors make a second payment. Still 11 payments, the minimum for these balances.
def owe(p): return -rounded[p]
settle = [
    {'from': 'mansi', 'to': 'gaurish', 'inr': rounded['gaurish']},
    {'from': 'mansi', 'to': 'ani', 'inr': owe('mansi') - rounded['gaurish']},
    {'from': 'kavya', 'to': 'nitye', 'inr': rounded['nitye']},
    {'from': 'kavya', 'to': 'ani', 'inr': owe('kavya') - rounded['nitye']},
]
to_bh = ['sumit', 'arnav', 'anushree', 'baid']
settle += [{'from': p, 'to': 'bhatnagar', 'inr': owe(p)} for p in to_bh]
rest_bh = rounded['bhatnagar'] - sum(owe(p) for p in to_bh)
settle += [{'from': 'sanket', 'to': 'bhatnagar', 'inr': rest_bh},
           {'from': 'sanket', 'to': 'ani', 'inr': owe('sanket') - rest_bh},
           {'from': 'nehal', 'to': 'ani', 'inr': owe('nehal')}]
assert all(x['inr'] > 0 for x in settle), settle
owes_total = {p: owe(p) for p in PEOPLE}
settle.sort(key=lambda x: (-owes_total[x['from']], -x['inr']))
for p in PEOPLE:
    moved = sum(s['inr'] for s in settle if s['to'] == p) - sum(s['inr'] for s in settle if s['from'] == p)
    check(f'settle {p}', moved, rounded[p])
check('settlements clear rounding within ₹1/person', max(abs(rounded[p] - net[p]) for p in PEOPLE), 0, tol=1.0)

print(f"\n{'person':10s} {'spent':>10s} {'paid':>10s} {'net':>10s}")
for p in sorted(PEOPLE, key=lambda p: -net[p]):
    print(f'{NAMES[p]:10s} {spent[p]:10,.0f} {paid[p]:10,.0f} {net[p]:+10,.0f}')
print(f"{'TOTAL':10s} {sum(spent.values()):10,.0f} {sum(paid.values()):10,.0f}")
print('\nSettle up:')
for s in settle: print(f"  {NAMES[s['from']]:10s} -> {NAMES[s['to']]:10s} ₹{s['inr']:,}")
print('\nALL CHECKS PASSED' if ok else '\nSOME CHECKS FAILED')
assert ok

out = {
    'trip': {'name': 'Abu Dhabi & Dubai', 'dates': '12–16 Nov 2026'},
    'rates': {'card': CARD_RATE, 'cash': DEFAULT_RATE, 'baid': BAID_RATE},
    'card': {'loadedAED': sum(a for a, _ in TOPUPS), 'loadedINR': sum(i for _, i in TOPUPS), 'withdrawnAED': WITHDRAW_AED,
             'withdrawnINR': WITHDRAW_INR, 'spentAED': CARD_SPENT_AED, 'ani': ANI_LOADED, 'bhatnagar': BHATNAGAR_LOADED},
    'people': [{'id': p, 'name': NAMES[p], 'spent': round(spent[p], 2), 'paid': round(paid[p], 2), 'net': round(net[p], 2)} for p in PEOPLE],
    'expenses': [{**e, 'inr': round(e['inr'], 2), 'shares': [{**a, 'inr': round(a['inr'], 2), 'aed': None if a['aed'] is None else round(a['aed'], 2)} for a in e['shares']]} for e in expenses],
    'payments': [{**p, 'inr': round(p['inr'], 2)} for p in payments],
    'settlements': settle,
    'totalSpent': round(sum(spent.values()), 2),
}
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data.json')
with open(path, 'w') as f: json.dump(out, f, ensure_ascii=False, indent=1)
print('wrote', os.path.normpath(path))
