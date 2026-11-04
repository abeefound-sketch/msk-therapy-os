"""
MSK-Therapy-OS V1.2 — Anatomical Binding System (ABS)
=====================================================
Unified interface exporting the canonical skeleton adapter, rigid bone bindings,
muscle deformation bindings, surface anchors, and the kinematic chain coordinator.
"""

from msk_therapy_os.canonical_skeleton_adapter import (
    CanonicalSkeletonAdapter,
    CanonicalBoneDef,
    Laterality,
    JointAxis,
    canonical_skeleton,
)
from msk_therapy_os.anatomical_binding.rigid_bone_binding import (
    RigidBoneBindingEntry,
    RigidBoneBindingAdapter,
    rigid_bone_adapter,
)
from msk_therapy_os.anatomical_binding.muscle_deformation_binding import (
    MuscleDeformationBindingEntry,
    MuscleDeformationAdapter,
    MuscleBiomechanicalState,
    DeformationStrategy,
    muscle_deformation_adapter,
)
from msk_therapy_os.anatomical_binding.surface_anchor_binding import (
    SurfaceAnchorEntry,
    SurfaceAnchorAdapter,
    surface_anchor_adapter,
)
from msk_therapy_os.anatomical_binding.kinematic_chain_coordinator import (
    KinematicChainCoordinator,
    ArmKinematicState,
    kinematic_coordinator,
)
from msk_therapy_os.anatomical_binding.universal_binding_schema import (
    AnatomicalStructureDefinition,
    StructureType,
    BindingStrategyType,
    RegistrationStatus,
    AttachmentLandmark,
    ValidationResult,
)
from msk_therapy_os.anatomical_binding.strategies import (
    BaseBindingStrategy,
    RigidBoneStrategy,
    MultiBoneSkinningStrategy,
    AttachmentDrivenDeformationStrategy,
    SurfaceBarycentricStrategy,
    MorphAwareRegistrationStrategy,
    get_strategy,
)
from msk_therapy_os.anatomical_binding.universal_anatomical_registry import (
    UniversalAnatomicalRegistry,
    universal_registry,
)
from msk_therapy_os.anatomical_binding.universal_coordinator import (
    UniversalKinematicCoordinator,
    UniversalKinematicState,
    universal_coordinator,
)

__all__ = [
    "CanonicalSkeletonAdapter",
    "CanonicalBoneDef",
    "Laterality",
    "JointAxis",
    "canonical_skeleton",
    "RigidBoneBindingEntry",
    "RigidBoneBindingAdapter",
    "rigid_bone_adapter",
    "MuscleDeformationBindingEntry",
    "MuscleDeformationAdapter",
    "MuscleBiomechanicalState",
    "DeformationStrategy",
    "muscle_deformation_adapter",
    "SurfaceAnchorEntry",
    "SurfaceAnchorAdapter",
    "surface_anchor_adapter",
    "KinematicChainCoordinator",
    "ArmKinematicState",
    "kinematic_coordinator",
    "AnatomicalStructureDefinition",
    "StructureType",
    "BindingStrategyType",
    "RegistrationStatus",
    "AttachmentLandmark",
    "ValidationResult",
    "BaseBindingStrategy",
    "RigidBoneStrategy",
    "MultiBoneSkinningStrategy",
    "AttachmentDrivenDeformationStrategy",
    "SurfaceBarycentricStrategy",
    "MorphAwareRegistrationStrategy",
    "get_strategy",
    "UniversalAnatomicalRegistry",
    "universal_registry",
    "UniversalKinematicCoordinator",
    "UniversalKinematicState",
    "universal_coordinator",
]
