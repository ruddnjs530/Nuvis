using RosMessageTypes.BuiltinInterfaces;
using RosMessageTypes.Geometry;
using RosMessageTypes.Std;
using Unity.Robotics.ROSTCPConnector;
using Unity.Robotics.ROSTCPConnector.ROSGeometry;
using UnityEngine;

public class RobotPosePublisher : MonoBehaviour
{
    [SerializeField] string m_TopicName = "/unity/robot_pose";
    [SerializeField] string m_FrameId = "unity";
    [SerializeField] double m_PublishRateHz = 20.0;

    ROSConnection m_Ros;
    double m_LastPublishTime;

    double PublishPeriodSeconds => 1.0 / Mathf.Max(1f, (float)m_PublishRateHz);
    static double NowSec => Time.realtimeSinceStartupAsDouble;
    bool ShouldPublish => NowSec - m_LastPublishTime >= PublishPeriodSeconds;

    void Start()
    {
        m_Ros = ROSConnection.GetOrCreateInstance();
        m_Ros.RegisterPublisher<PoseStampedMsg>(m_TopicName);
        m_LastPublishTime = NowSec - PublishPeriodSeconds;
    }

    void Update()
    {
        if (!ShouldPublish)
            return;

        PublishPose();
        m_LastPublishTime = NowSec;
    }

    void PublishPose()
    {
        var positionFlu = transform.position.To<FLU>();
        var rotationFlu = transform.rotation.To<FLU>();
        var now = NowSec;
        var sec = (int)now;
        var nsec = (uint)((now - sec) * 1e9);

        var msg = new PoseStampedMsg
        {
            header = new HeaderMsg
            {
                frame_id = m_FrameId,
                stamp = new TimeMsg
                {
                    sec = sec,
                    nanosec = nsec,
                }
            },
            pose = new PoseMsg
            {
                position = new PointMsg(positionFlu.x, positionFlu.y, positionFlu.z),
                orientation = new QuaternionMsg(
                    rotationFlu.x,
                    rotationFlu.y,
                    rotationFlu.z,
                    rotationFlu.w
                ),
            }
        };

        m_Ros.Publish(m_TopicName, msg);
    }
}
