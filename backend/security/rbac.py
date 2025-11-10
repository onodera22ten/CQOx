"""
Role-Based Access Control (RBAC) - NASA/Google Standard

Purpose: Fine-grained access control system
Features:
- Hierarchical roles
- Resource-based permissions
- Action-based permissions
- Dynamic permission checking
- Permission inheritance
"""

from enum import Enum
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status


class Permission(str, Enum):
    """Base permissions"""
    # Dataset permissions
    DATASET_CREATE = "dataset:create"
    DATASET_READ = "dataset:read"
    DATASET_UPDATE = "dataset:update"
    DATASET_DELETE = "dataset:delete"
    DATASET_SHARE = "dataset:share"

    # Job permissions
    JOB_CREATE = "job:create"
    JOB_READ = "job:read"
    JOB_CANCEL = "job:cancel"
    JOB_DELETE = "job:delete"

    # Analysis permissions
    ANALYSIS_RUN = "analysis:run"
    ANALYSIS_READ = "analysis:read"
    ANALYSIS_EXPORT = "analysis:export"

    # Policy permissions
    POLICY_CREATE = "policy:create"
    POLICY_READ = "policy:read"
    POLICY_UPDATE = "policy:update"
    POLICY_DELETE = "policy:delete"
    POLICY_DEPLOY = "policy:deploy"

    # Admin permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"

    # API permissions
    API_KEY_CREATE = "api_key:create"
    API_KEY_REVOKE = "api_key:revoke"


class Role(str, Enum):
    """Predefined roles"""
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"
    GUEST = "guest"


@dataclass
class RoleDefinition:
    """Role definition with permissions"""
    name: str
    permissions: Set[Permission]
    inherits_from: Optional[List[str]] = None
    description: str = ""


class RBACManager:
    """
    RBAC Manager

    Manages roles, permissions, and access control
    """

    def __init__(self):
        self.roles: Dict[str, RoleDefinition] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default role definitions"""

        # Guest role - minimal read access
        self.roles[Role.GUEST] = RoleDefinition(
            name=Role.GUEST,
            permissions={
                Permission.DATASET_READ,
                Permission.ANALYSIS_READ
            },
            description="Read-only guest access"
        )

        # Viewer role - read all
        self.roles[Role.VIEWER] = RoleDefinition(
            name=Role.VIEWER,
            permissions={
                Permission.DATASET_READ,
                Permission.JOB_READ,
                Permission.ANALYSIS_READ,
                Permission.POLICY_READ,
            },
            inherits_from=[Role.GUEST],
            description="Read access to all resources"
        )

        # Analyst role - can run analysis
        self.roles[Role.ANALYST] = RoleDefinition(
            name=Role.ANALYST,
            permissions={
                Permission.DATASET_CREATE,
                Permission.DATASET_UPDATE,
                Permission.JOB_CREATE,
                Permission.JOB_CANCEL,
                Permission.ANALYSIS_RUN,
                Permission.ANALYSIS_EXPORT,
                Permission.POLICY_READ,
            },
            inherits_from=[Role.VIEWER],
            description="Can create datasets and run analysis"
        )

        # Data Scientist role - full analysis capabilities
        self.roles[Role.DATA_SCIENTIST] = RoleDefinition(
            name=Role.DATA_SCIENTIST,
            permissions={
                Permission.DATASET_DELETE,
                Permission.DATASET_SHARE,
                Permission.JOB_DELETE,
                Permission.POLICY_CREATE,
                Permission.POLICY_UPDATE,
                Permission.POLICY_DELETE,
                Permission.API_KEY_CREATE,
            },
            inherits_from=[Role.ANALYST],
            description="Full data science capabilities"
        )

        # API User role - programmatic access
        self.roles[Role.API_USER] = RoleDefinition(
            name=Role.API_USER,
            permissions={
                Permission.DATASET_CREATE,
                Permission.DATASET_READ,
                Permission.JOB_CREATE,
                Permission.JOB_READ,
                Permission.ANALYSIS_RUN,
                Permission.ANALYSIS_READ,
            },
            description="API access for programmatic usage"
        )

        # Admin role - full system access
        self.roles[Role.ADMIN] = RoleDefinition(
            name=Role.ADMIN,
            permissions=set(Permission),  # All permissions
            inherits_from=[Role.DATA_SCIENTIST],
            description="Full system administrator"
        )

    def get_role_permissions(self, role_name: str) -> Set[Permission]:
        """
        Get all permissions for a role (including inherited)

        Args:
            role_name: Role name

        Returns:
            Set of permissions
        """
        if role_name not in self.roles:
            return set()

        role = self.roles[role_name]
        permissions = role.permissions.copy()

        # Add inherited permissions
        if role.inherits_from:
            for parent_role in role.inherits_from:
                permissions.update(self.get_role_permissions(parent_role))

        return permissions

    def has_permission(self, role_name: str, permission: Permission) -> bool:
        """
        Check if role has specific permission

        Args:
            role_name: Role name
            permission: Permission to check

        Returns:
            True if role has permission
        """
        permissions = self.get_role_permissions(role_name)
        return permission in permissions

    def check_permission(
        self,
        user_role: str,
        required_permission: Permission,
        raise_exception: bool = True
    ) -> bool:
        """
        Check permission and optionally raise exception

        Args:
            user_role: User's role
            required_permission: Required permission
            raise_exception: Whether to raise exception if denied

        Returns:
            True if authorized

        Raises:
            HTTPException if not authorized and raise_exception=True
        """
        has_perm = self.has_permission(user_role, required_permission)

        if not has_perm and raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}"
            )

        return has_perm

    def check_any_permission(
        self,
        user_role: str,
        required_permissions: List[Permission],
        raise_exception: bool = True
    ) -> bool:
        """Check if user has any of the required permissions"""
        user_permissions = self.get_role_permissions(user_role)

        has_any = any(perm in user_permissions for perm in required_permissions)

        if not has_any and raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required one of: {required_permissions}"
            )

        return has_any

    def check_all_permissions(
        self,
        user_role: str,
        required_permissions: List[Permission],
        raise_exception: bool = True
    ) -> bool:
        """Check if user has all required permissions"""
        user_permissions = self.get_role_permissions(user_role)

        has_all = all(perm in user_permissions for perm in required_permissions)

        if not has_all and raise_exception:
            missing = [p for p in required_permissions if p not in user_permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Missing: {missing}"
            )

        return has_all

    def add_custom_role(
        self,
        role_name: str,
        permissions: Set[Permission],
        inherits_from: Optional[List[str]] = None,
        description: str = ""
    ):
        """Add custom role definition"""
        self.roles[role_name] = RoleDefinition(
            name=role_name,
            permissions=permissions,
            inherits_from=inherits_from,
            description=description
        )

    def get_role_hierarchy(self) -> Dict[str, List[str]]:
        """Get role hierarchy (role -> parent roles)"""
        hierarchy = {}
        for role_name, role_def in self.roles.items():
            hierarchy[role_name] = role_def.inherits_from or []
        return hierarchy


# Singleton RBAC manager
rbac_manager = RBACManager()


# ===== FastAPI Permission Checkers =====

class PermissionChecker:
    """
    FastAPI dependency for permission checking

    Usage:
        @router.post("/datasets")
        async def create_dataset(
            user = Depends(get_current_user),
            _ = Depends(PermissionChecker(Permission.DATASET_CREATE))
        ):
            ...
    """

    def __init__(self, required_permission: Permission):
        self.required_permission = required_permission

    def __call__(self, user: Dict):
        """Check permission"""
        user_role = user.get("role", "guest")
        rbac_manager.check_permission(user_role, self.required_permission)
        return user


class AnyPermissionChecker:
    """Check if user has any of the required permissions"""

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    def __call__(self, user: Dict):
        user_role = user.get("role", "guest")
        rbac_manager.check_any_permission(user_role, self.required_permissions)
        return user


class AllPermissionsChecker:
    """Check if user has all required permissions"""

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    def __call__(self, user: Dict):
        user_role = user.get("role", "guest")
        rbac_manager.check_all_permissions(user_role, self.required_permissions)
        return user


# ===== Resource-Based Access Control =====

@dataclass
class ResourceOwnership:
    """Resource ownership record"""
    resource_type: str  # "dataset", "job", "policy"
    resource_id: str
    owner_id: str
    shared_with: List[str] = None  # List of user IDs with access
    created_at: datetime = None


class ResourceAccessManager:
    """
    Resource-based access control

    Checks ownership and sharing permissions
    """

    def __init__(self):
        # In production, this would query database
        self.ownership_db: Dict[str, ResourceOwnership] = {}

    def set_owner(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str
    ):
        """Set resource owner"""
        key = f"{resource_type}:{resource_id}"
        self.ownership_db[key] = ResourceOwnership(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            shared_with=[],
            created_at=datetime.utcnow()
        )

    def check_access(
        self,
        user_id: str,
        user_role: str,
        resource_type: str,
        resource_id: str,
        required_permission: Permission,
        raise_exception: bool = True
    ) -> bool:
        """
        Check if user can access resource

        Access granted if:
        1. User is admin
        2. User is owner
        3. Resource is shared with user
        4. User has required permission

        Args:
            user_id: User ID
            user_role: User role
            resource_type: Resource type
            resource_id: Resource ID
            required_permission: Required permission
            raise_exception: Raise exception if denied

        Returns:
            True if access granted
        """
        # Admins have full access
        if user_role == Role.ADMIN:
            return True

        # Check role permission
        if not rbac_manager.has_permission(user_role, required_permission):
            if raise_exception:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {required_permission}"
                )
            return False

        # Check ownership
        key = f"{resource_type}:{resource_id}"
        ownership = self.ownership_db.get(key)

        if not ownership:
            # Resource not found or no ownership set
            # Allow if user has permission
            return True

        # Owner has full access
        if ownership.owner_id == user_id:
            return True

        # Check if shared
        if ownership.shared_with and user_id in ownership.shared_with:
            return True

        # Access denied
        if raise_exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {resource_type} {resource_id}"
            )

        return False

    def share_resource(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str,
        share_with_user_id: str
    ):
        """Share resource with another user"""
        key = f"{resource_type}:{resource_id}"
        ownership = self.ownership_db.get(key)

        if not ownership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource not found: {resource_type}:{resource_id}"
            )

        if ownership.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can share resource"
            )

        if not ownership.shared_with:
            ownership.shared_with = []

        if share_with_user_id not in ownership.shared_with:
            ownership.shared_with.append(share_with_user_id)


# Singleton resource access manager
resource_access_manager = ResourceAccessManager()
