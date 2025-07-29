# Dynamic Preference Banking and Conflict Resolution System

## Executive Summary

This document outlines a proposed extension to the dermatopathology scheduler that introduces social dynamics and fairness mechanisms through a preference banking system, advanced conflict resolution algorithms, and trust-based scheduling. The system transforms scheduling from a pure optimization problem into a social coordination mechanism that builds trust and fairness over time.

## Table of Contents

1. [Overview](#overview)
2. [Dynamic Banking System for Preference Trading](#dynamic-banking-system)
3. [Conflict Resolution Algorithms](#conflict-resolution-algorithms)
4. [Running Debt Equalization System](#running-debt-equalization)
5. [Trust-Based Time Horizons](#trust-based-time-horizons)
6. [Soft Constraints and Implicit Preferences](#soft-constraints)
7. [Architecture and Implementation](#architecture-implementation)
8. [Integration Strategy](#integration-strategy)
9. [Future Considerations](#future-considerations)

## Overview {#overview}

The proposed system extends the current scheduling framework with:

- **Preference Credits**: A currency system for tracking sacrifices and favors
- **Conflict Resolution**: Multiple algorithms for fairly resolving scheduling conflicts
- **Long-term Fairness**: Multi-year tracking and equalization of sacrifices
- **Trust Networks**: Personalized lending terms based on peer relationships
- **Implicit Preferences**: Encoding unspoken rules and system knowledge

## Dynamic Banking System for Preference Trading {#dynamic-banking-system}

### Core Concepts

The preference banking system tracks when physicians give up their preferences and accumulates "credits" they can use later.

#### Data Models

```python
@dataclass
class PreferenceCredit:
    """Represents a credit earned by giving up a preference"""
    creditor: str  # Who earned the credit
    debtor: str    # Who benefited (could be "pool" for general sacrifices)
    amount: float  # Credit value
    date_earned: date
    expiry_date: Optional[date]  # Credits could expire
    preference_type: str  # vacation, sdo, role_preference, etc.
    context: Dict[str, Any]  # Additional metadata

@dataclass
class CreditBalance:
    """Tracks credit relationships between physicians"""
    physician: str
    credits_earned: List[PreferenceCredit]
    credits_owed: List[PreferenceCredit]
    net_balance: Dict[str, float]  # Balance per other physician
```

### Credit Valuation Framework

Different sacrifices have different values:

| Sacrifice Type | Base Credit Value | Multipliers |
|---------------|------------------|-------------|
| Holiday Coverage | 10.0 | 2x for major holidays |
| Weekend Coverage | 5.0 | 1.5x for long weekends |
| SDO Sacrifice | 3.0 | 2x if < 24hr notice |
| Undesirable Role | 2.0 | Varies by role |
| Schedule Change | 1.0 | Based on disruption |

### Credit Lifecycle

1. **Earning**: Credits earned when giving up preferences
2. **Banking**: Credits stored with optional expiration
3. **Spending**: Credits used to secure future preferences
4. **Transfer**: Credits can be traded between physicians
5. **Expiration**: Unused credits may expire to encourage use

## Conflict Resolution Algorithms {#conflict-resolution-algorithms}

When multiple physicians request the same time off, the system employs one of several resolution strategies:

### 1. Weighted Lottery System

**Concept**: Probabilistic selection weighted by multiple factors

**Implementation**:
```python
class WeightedLotteryResolver:
    def calculate_weight(self, physician, request):
        weight = 1.0
        weight *= (1 + credit_balance / 100)  # Credit influence
        weight *= (1 + seniority_years / 20)   # Seniority factor
        weight *= urgency_multiplier           # Request urgency
        weight *= fairness_multiplier          # Recent wins penalty
        return weight
```

**Pros**: 
- Balances multiple factors
- Gives everyone a chance
- Prevents monopolization

**Cons**:
- Less predictable
- May feel arbitrary

### 2. Rotating Priority Wheel

**Concept**: Deterministic rotation ensuring everyone gets turns

**Implementation**:
- Maintain ordered queue of physicians
- Winner moves to back of queue
- Track "win" history for transparency

**Pros**:
- Highly predictable
- Guaranteed fairness over time
- Simple to understand

**Cons**:
- Doesn't account for urgency
- Inflexible to special circumstances

### 3. Credit Auction System

**Concept**: Market-based approach using preference credits

**Process**:
1. Physicians submit sealed bids in credits
2. Highest bidder wins the slot
3. Winner's credits distributed to losers as compensation
4. Minimum bid requirements prevent hoarding

**Pros**:
- Efficient allocation to those who value most
- Self-regulating through market forces
- Compensates those who lose out

**Cons**:
- Requires credit accumulation
- May favor those who sacrifice more

### 4. Nash Bargaining Solution

**Concept**: Maximize overall social welfare while maintaining fairness

**Algorithm**:
- Calculate utility impact for each possible assignment
- Find allocation that maximizes product of utilities
- Ensure Pareto efficiency
- Apply envy-freeness constraints

**Pros**:
- Theoretically optimal fairness
- Considers global impact
- Well-studied approach

**Cons**:
- Computationally intensive
- Requires accurate utility functions

### 5. Hybrid Approaches

Combine multiple algorithms based on context:

| Scenario | Primary Algorithm | Secondary |
|----------|------------------|-----------|
| Regular days off | Priority Wheel | Lottery for ties |
| Holiday periods | Credit Auction | Nash if disputed |
| Emergency coverage | Weighted Lottery | Credit bonus |
| Vacation blocks | Seniority + Credits | Auction fallback |

## Running Debt Equalization System {#running-debt-equalization}

### Multi-Year Fairness Tracking

The system maintains a rolling window of sacrifice history to ensure long-term fairness:

```python
class EqualizationEngine:
    def __init__(self, window_years=3):
        self.window = window_years
        self.target_balance = 0  # Everyone should tend toward zero
    
    def calculate_deviation(self, physician):
        """How far from fair share of sacrifices"""
        personal_score = sum(sacrifices in window)
        group_average = mean(all physicians' scores)
        return personal_score - group_average
```

### Equalization Strategies

1. **Soft Rebalancing**: Gradual preference toward those with positive deviation
2. **Hard Limits**: Maximum deviation before mandatory compensation
3. **Periodic Reconciliation**: Annual or semi-annual balance reviews

### Metrics and Reporting

- **Sacrifice Balance Score**: Individual deviation from group average
- **Gini Coefficient**: Overall inequality measure
- **Trend Analysis**: Direction and rate of balance changes
- **Predictive Modeling**: Forecast future imbalances

## Trust-Based Time Horizons {#trust-based-time-horizons}

### Trust Network Model

Physicians can set different lending terms based on trust relationships:

```python
class TrustRelationship:
    from_physician: str
    to_physician: str
    trust_level: float  # 0.0 to 1.0
    repayment_horizon: timedelta
    max_credit_limit: float
    interest_rate: float  # For credit decay
```

### Trust Factors

1. **Historical Reliability**: Past repayment behavior
2. **Peer Ratings**: Explicit trust scores
3. **Collaboration Frequency**: How often they work together
4. **Reciprocity Index**: Balance of past exchanges

### Lending Terms by Trust Level

| Trust Level | Repayment Horizon | Credit Limit | Interest Rate |
|------------|------------------|--------------|---------------|
| Very High (0.9-1.0) | 6 months | 100 credits | 0% |
| High (0.7-0.9) | 3 months | 50 credits | 5% |
| Medium (0.5-0.7) | 1 month | 25 credits | 10% |
| Low (0.3-0.5) | 2 weeks | 10 credits | 20% |
| Minimal (<0.3) | Immediate | 5 credits | 50% |

## Soft Constraints and Implicit Preferences {#soft-constraints}

### Types of Soft Constraints

1. **Skill-Based Preferences**
   ```python
   # Encode implicit knowledge about physician capabilities
   skill_matrix = {
       ("Dr. Smith", Role.COMPLEX_CASES): 0.9,
       ("Dr. Smith", Role.ROUTINE): 0.5,  # Overqualified
       ("Dr. Jones", Role.TEACHING): 0.8,
       ("Dr. Jones", Role.COMPLEX_CASES): 0.6
   }
   ```

2. **Workload Preferences**
   - Some physicians prefer consistent moderate load
   - Others prefer intense periods with more time off
   - System learns and adapts to individual patterns

3. **Team Dynamics**
   - Certain pairs work well together
   - Some combinations should be avoided
   - Mentorship relationships prioritized

4. **Hidden Fairness Rules**
   - Senior physicians get first choice on major holidays
   - Junior physicians protected from too many weekends
   - Implicit "dues paying" for new members

### Implementation in Scheduler

Soft constraints integrated as weighted penalties in objective function:

```python
total_penalty = sum(
    constraint.weight * constraint.evaluate(schedule)
    for constraint in soft_constraints
)

# Minimize: original_objective + lambda * total_penalty
```

## Architecture and Implementation {#architecture-implementation}

### System Components

1. **Credit Service**
   - Manages credit lifecycle
   - Handles transactions
   - Enforces rules and limits

2. **Conflict Resolution Engine**
   - Implements multiple algorithms
   - Selects appropriate strategy
   - Executes resolution

3. **Trust Network Manager**
   - Maintains relationship graph
   - Calculates trust scores
   - Updates based on interactions

4. **Fairness Monitor**
   - Tracks long-term balances
   - Generates alerts
   - Produces reports

5. **Preference Learning Module**
   - Observes patterns
   - Updates soft constraints
   - Improves predictions

### Database Schema

```sql
-- Core tables
CREATE TABLE preference_credits (
    id UUID PRIMARY KEY,
    creditor_id VARCHAR(50),
    debtor_id VARCHAR(50),
    amount DECIMAL(10,2),
    type VARCHAR(20),
    earned_date DATE,
    expiry_date DATE,
    metadata JSONB
);

CREATE TABLE trust_relationships (
    from_physician_id VARCHAR(50),
    to_physician_id VARCHAR(50),
    trust_score DECIMAL(3,2),
    last_updated TIMESTAMP,
    PRIMARY KEY (from_physician_id, to_physician_id)
);

CREATE TABLE sacrifice_history (
    id UUID PRIMARY KEY,
    physician_id VARCHAR(50),
    sacrifice_date DATE,
    type VARCHAR(20),
    value DECIMAL(10,2),
    beneficiaries JSONB
);
```

### API Design

```yaml
/api/v1/credits:
  GET:
    - /balance/{physician_id}
    - /history/{physician_id}
    - /pending_transfers
  POST:
    - /transfer
    - /earn
    - /spend

/api/v1/conflicts:
  POST:
    - /resolve
    - /simulate
  GET:
    - /strategies
    - /history

/api/v1/trust:
  GET:
    - /network
    - /relationship/{from}/{to}
  PUT:
    - /relationship
```

## Integration Strategy {#integration-strategy}

### Phase 1: Foundation (Months 1-3)
- Implement basic credit system
- Add simple conflict resolution (lottery/rotation)
- Create database schema
- Build basic APIs

### Phase 2: Trust and Learning (Months 4-6)
- Add trust network
- Implement credit auction system
- Integrate soft constraints
- Begin pattern learning

### Phase 3: Advanced Features (Months 7-9)
- Multi-year equalization
- Nash bargaining implementation
- Advanced analytics
- Mobile app integration

### Phase 4: Optimization (Months 10-12)
- Performance tuning
- Machine learning enhancements
- User feedback integration
- System refinements

## Future Considerations {#future-considerations}

### Potential Enhancements

1. **Blockchain Integration**: Immutable ledger for credit transactions
2. **ML-Powered Predictions**: Anticipate conflicts before they occur
3. **Gamification**: Badges and achievements for good citizens
4. **Cross-Department Trading**: Expand beyond single department
5. **Real-time Negotiation**: Live trading during conflicts

### Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gaming the system | High | Audit trails, limits, peer review |
| Credit inflation | Medium | Automatic decay, caps, reset periods |
| Trust manipulation | Medium | Multi-factor trust, slow adjustments |
| Complexity overload | High | Phased rollout, training, simple defaults |
| Technical debt | Medium | Modular design, regular refactoring |

### Success Metrics

1. **Fairness Metrics**
   - Gini coefficient < 0.3
   - Sacrifice variance < 20%
   - Satisfaction scores > 80%

2. **System Metrics**
   - Conflict resolution time < 2 minutes
   - Credit transaction success > 99.9%
   - API response time < 200ms

3. **User Metrics**
   - Active users > 90%
   - Credit utilization 40-60%
   - Trust network density > 0.5

## Conclusion

The proposed preference banking and conflict resolution system represents a paradigm shift in medical scheduling. By introducing economic and social mechanisms, we can create a more fair, transparent, and satisfying scheduling experience that adapts to the complex human dynamics of a medical practice.

The system balances algorithmic efficiency with human judgment, creating a sustainable solution that improves over time. Through careful implementation and monitoring, this system can serve as a model for fair resource allocation in complex organizational settings.