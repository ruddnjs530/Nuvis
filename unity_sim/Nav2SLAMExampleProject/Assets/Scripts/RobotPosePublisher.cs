using RosMessageTypes.BuiltinInterfaces;
using RosMessageTypes.Geometry;
using RosMessageTypes.Std;
using Unity.Robotics.Core;
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

    double PublishPeriodSeconds => 1.0f / Mathf.Max(1f, (float)m_PublishRateHz);
    bool ShouldPublish => Clock.NowTimeInSeconds - m_LastPublishTime >= PublishPeriodSeconds;

    void Start()
    {
        m_Ros = ROSConnection.GetOrCreateInstance();
        m_Ros.RegisterPublisher<PoseStampedMsg>(m_TopicName);
        m_LastPublishTime = Clock.NowTimeInSeconds;
    }

    void Update()
    {
        if (!ShouldPublish)
            return;

        PublishPose();
        m_LastPublishTime = Clock.NowTimeInSeconds;
    }

    void PublishPose()
    {
        var positionFlu = transform.position.To<FLU>();
        var rotationFlu = transform.rotation.To<FLU>();
        var timestamp = new TimeStamp(Clock.time);

        var msg = new PoseStampedMsg
        {
            header = new HeaderMsg
            {
                frame_id = m_FrameId,
                stamp = new TimeMsg
                {
                    sec = timestamp.Seconds,
                    nanosec = timestamp.NanoSeconds,
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
