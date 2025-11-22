"""
API Gateway - Domain Models
Pure business entities without framework dependencies
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    INACTIVE = "inactive"
    CIRCUIT_OPEN = "circuit_open"


class OAuthPlatform(str, Enum):
    """Supported OAuth platforms"""
    GOOGLE = "google"
    LINKEDIN = "linkedin"
    META = "meta"
    TWITTER = "twitter"
    TIKTOK = "tiktok"


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ServiceNode:
    """
    Represents a service instance in the ecosystem

    Domain Entity: Encapsulates service routing and health
    """
    name: str
    url: str
    weight: float = 1.0
    status: ServiceStatus = ServiceStatus.ACTIVE
    response_time_ms: float = 0.0
    error_count: int = 0
    success_count: int = 0
    last_check: Optional[datetime] = None

    def calculate_health_score(self) -> float:
        """
        Calculate service health score (0-100)

        Business Rule: Health = (success_rate * 0.7) + (response_time_factor * 0.3)
        """
        total_requests = self.success_count + self.error_count

        if total_requests == 0:
            return 100.0

        # Success rate component (70% weight)
        success_rate = (self.success_count / total_requests) * 100

        # Response time component (30% weight)
        # Good: < 100ms, Acceptable: < 500ms, Bad: > 500ms
        if self.response_time_ms < 100:
            response_score = 100.0
        elif self.response_time_ms < 500:
            response_score = 80.0 - ((self.response_time_ms - 100) / 400 * 30)
        else:
            response_score = max(0, 50 - ((self.response_time_ms - 500) / 500 * 50))

        health_score = (success_rate * 0.7) + (response_score * 0.3)

        return round(min(100.0, max(0.0, health_score)), 2)

    def should_use(self) -> bool:
        """
        Business Rule: Should this node receive traffic?
        """
        return (
            self.status == ServiceStatus.ACTIVE and
            self.calculate_health_score() > 30 and
            self.error_count < 10
        )

    def record_success(self, response_time_ms: float) -> None:
        """Record successful request"""
        self.success_count += 1
        self.response_time_ms = (
            (self.response_time_ms * 0.7) + (response_time_ms * 0.3)
        )  # Exponential moving average
        self.last_check = datetime.utcnow()

        # Auto-recovery logic
        if self.status == ServiceStatus.DEGRADED and self.calculate_health_score() > 70:
            self.status = ServiceStatus.ACTIVE

    def record_failure(self) -> None:
        """Record failed request"""
        self.error_count += 1
        self.last_check = datetime.utcnow()

        # Auto-degradation logic
        if self.error_count > 5 and self.calculate_health_score() < 50:
            self.status = ServiceStatus.DEGRADED


@dataclass
class CircuitBreaker:
    """
    Circuit Breaker pattern implementation

    Domain Entity: Protects against cascading failures
    """
    service_name: str
    state: CircuitState = CircuitState.CLOSED
    failure_threshold: int = 5
    timeout_seconds: int = 60
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.utcnow)

    def record_success(self) -> None:
        """Record successful call"""
        self.success_count += 1
        self.failure_count = 0

        # Transition from HALF_OPEN to CLOSED after successful calls
        if self.state == CircuitState.HALF_OPEN and self.success_count >= 3:
            self._transition_to_closed()

    def record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        # Transition to OPEN if threshold exceeded
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self._transition_to_open()

        # Back to OPEN if HALF_OPEN test fails
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()

    def can_attempt(self) -> bool:
        """
        Business Rule: Should we attempt this call?

        Returns:
            True if call should be attempted, False if circuit is open
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    self._transition_to_half_open()
                    return True
            return False

        # HALF_OPEN: allow limited attempts
        return True

    def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change = datetime.utcnow()

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = datetime.utcnow()


@dataclass
class OAuthToken:
    """
    OAuth 2.0 Token

    Domain Entity: Represents authenticated user token
    """
    platform: OAuthPlatform
    user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    token_type: str = "Bearer"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """
        Business Rule: Is this token expired?
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def is_valid(self) -> bool:
        """
        Business Rule: Is this token valid for use?
        """
        return not self.is_expired() and len(self.access_token) > 0

    def should_refresh(self, buffer_minutes: int = 5) -> bool:
        """
        Business Rule: Should we refresh this token proactively?

        Args:
            buffer_minutes: Refresh buffer time before expiry
        """
        if self.expires_at is None or self.refresh_token is None:
            return False

        buffer_time = datetime.utcnow() + timedelta(minutes=buffer_minutes)
        return buffer_time >= self.expires_at


@dataclass
class OAuthState:
    """
    OAuth authorization state

    Value Object: Represents pending OAuth flow
    """
    state_token: str
    platform: OAuthPlatform
    user_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    code_verifier: Optional[str] = None  # For PKCE (Twitter)
    redirect_uri: Optional[str] = None

    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """
        Business Rule: OAuth state expires after timeout
        """
        elapsed = datetime.utcnow() - self.created_at
        return elapsed > timedelta(minutes=timeout_minutes)

    def is_valid(self) -> bool:
        """Check if state is valid"""
        return not self.is_expired()


@dataclass
class RouteDecision:
    """
    Routing decision made by the gateway

    Value Object: Immutable routing decision
    """
    service_name: str
    target_url: str
    decision_method: str  # "round_robin", "weighted", "rl_engine"
    confidence: float  # 0.0 - 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "service": self.service_name,
            "url": self.target_url,
            "method": self.decision_method,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CacheEntry:
    """
    Cache entry with TTL

    Value Object: Cached response data
    """
    key: str
    data: Any
    ttl_seconds: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed >= self.ttl_seconds

    def is_valid(self) -> bool:
        """Check if cache entry is valid"""
        return not self.is_expired()

    def increment_hit(self) -> None:
        """Increment hit counter"""
        self.hit_count += 1


# Domain exceptions

class DomainException(Exception):
    """Base exception for domain errors"""
    pass


class ServiceUnavailableError(DomainException):
    """Service is not available for routing"""
    pass


class CircuitBreakerOpenError(DomainException):
    """Circuit breaker is open, blocking requests"""
    pass


class InvalidTokenError(DomainException):
    """OAuth token is invalid or expired"""
    pass


class InvalidStateError(DomainException):
    """OAuth state is invalid or expired"""
    pass
