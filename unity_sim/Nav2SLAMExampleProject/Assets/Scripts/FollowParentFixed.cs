using UnityEngine;

public class FollowParentFixed : MonoBehaviour
{
    [SerializeField] private Transform targetParent;
    [SerializeField] private Vector3 localPosition;
    [SerializeField] private Vector3 localEulerAngles;

    void LateUpdate()
    {
        if (targetParent == null) return;

        transform.position = targetParent.TransformPoint(localPosition);
        transform.rotation = targetParent.rotation * Quaternion.Euler(localEulerAngles);
    }
}