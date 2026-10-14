#include "spl_behavior.h"

#include <nitro/fx/fx.h>
#include <nitro/fx/fx_mtx33.h>
#include <nitro/fx/fx_trig.h>

#include "spl_random.h"

void SPLBehavior_ApplyGravity(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLGravityBehavior *gravity = (SPLGravityBehavior *)obj;
    acc->x += gravity->magnitude.x;
    acc->y += gravity->magnitude.y;
    acc->z += gravity->magnitude.z;
}

void SPLBehavior_ApplyRandom(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLRandomBehavior *rng = (SPLRandomBehavior *)obj;
    if ((ptcl->age % (rng->applyInterval * emtr->timeScale)) == 0) {
        acc->x += SPLRandom_RangeFX32(rng->magnitude.x);
        acc->y += SPLRandom_RangeFX32(rng->magnitude.y);
        acc->z += SPLRandom_RangeFX32(rng->magnitude.z);
    }
}

void SPLBehavior_ApplyMagnet(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLMagnetBehavior *magnet = (SPLMagnetBehavior *)obj;
    acc->x += (magnet->force * ((magnet->target.x - ptcl->position.x) - ptcl->velocity.x)) >> FX32_SHIFT;
    acc->y += (magnet->force * ((magnet->target.y - ptcl->position.y) - ptcl->velocity.y)) >> FX32_SHIFT;
    acc->z += (magnet->force * ((magnet->target.z - ptcl->position.z) - ptcl->velocity.z)) >> FX32_SHIFT;
}

void SPLBehavior_ApplySpin(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLSpinBehavior *spin = (SPLSpinBehavior *)obj;
    MtxFx33 rot;

    // Sour Platinum: this runs on every update, so each update turns by its share of the original angle
    u16 angle = (s16)spin->angle / emtr->timeScale;

    switch (spin->axis) {
    case SPL_SPIN_BEHAVIOR_AXIS_X:
        MTX_RotX33(&rot, FX_SinIdx(angle), FX_CosIdx(angle));
        break;
    case SPL_SPIN_BEHAVIOR_AXIS_Y:
        MTX_RotY33(&rot, FX_SinIdx(angle), FX_CosIdx(angle));
        break;
    case SPL_SPIN_BEHAVIOR_AXIS_Z:
        MTX_RotZ33(&rot, FX_SinIdx(angle), FX_CosIdx(angle));
        break;
    }

    MTX_MultVec33(&ptcl->position, &rot, &ptcl->position);
}

void SPLBehavior_ApplyCollisionPlane(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLCollisionPlaneBehavior *plane = (SPLCollisionPlaneBehavior *)obj;
    fx32 y = plane->y;
    fx32 ey;

    if (emtr->collisionPlaneHeight != FX32_MIN) {
        y = emtr->collisionPlaneHeight;
    }

    switch (plane->collisionType) {
    case SPL_COLLISION_BEHAVIOR_TYPE_KILL:
        ey = ptcl->emitterPos.y;
        if (ey < y && ey + ptcl->position.y > y) {
            ptcl->position.y = y - ey;
            ptcl->age = ptcl->lifeTime;
        } else if (ey >= y && ey + ptcl->position.y < y) {
            ptcl->position.y = y - ey;
            ptcl->age = ptcl->lifeTime;
        }
        break;
    case SPL_COLLISION_BEHAVIOR_TYPE_BOUNCE:
        ey = ptcl->emitterPos.y;
        if (ey < y && ey + ptcl->position.y > y) {
            ptcl->position.y = y - ey;
            ptcl->velocity.y = -FX32_CAST(FX_MUL(ptcl->velocity.y, plane->elasticity));
        } else if (ey >= y && ey + ptcl->position.y < y) {
            ptcl->position.y = y - ey;
            ptcl->velocity.y = -FX32_CAST(FX_MUL(ptcl->velocity.y, plane->elasticity));
        }
        break;
    }
}

void SPLBehavior_ApplyConvergence(const void *obj, SPLParticle *ptcl, VecFx32 *acc, SPLEmitter *emtr)
{
    SPLConvergenceBehavior *conv = (SPLConvergenceBehavior *)obj;

    // Sour Platinum: this runs on every update, so each update moves by its share of the original step
    ptcl->position.x += FX32_CAST(FX_MUL(conv->force, (conv->target.x - ptcl->position.x))) / emtr->timeScale;
    ptcl->position.y += FX32_CAST(FX_MUL(conv->force, (conv->target.y - ptcl->position.y))) / emtr->timeScale;
    ptcl->position.z += FX32_CAST(FX_MUL(conv->force, (conv->target.z - ptcl->position.z))) / emtr->timeScale;
}
