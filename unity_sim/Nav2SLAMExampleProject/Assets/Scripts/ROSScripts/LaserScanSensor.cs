using System;
using System.Collections.Generic;
using RosMessageTypes.Sensor;
using RosMessageTypes.Std;
using RosMessageTypes.BuiltinInterfaces;
using Unity.Robotics.Core;
using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using UnityEngine.Serialization;
using System.Linq;

public class LaserScanSensor : MonoBehaviour
{
    public string topic = "/scan";
    [FormerlySerializedAs("TimeBetweenScansSeconds")]
    public double PublishPeriodSeconds = 0.1;
    public float RangeMetersMin = 0;
    public float RangeMetersMax = 1000;
    public float ScanAngleStartDegrees = -180;
    public float ScanAngleEndDegrees = 180;
    // Change the scan start and end by this amount after every publish
    public float ScanOffsetAfterPublish = 0f;
    public int NumMeasurementsPerScan = 180;
    public float TimeBetweenMeasurementsSeconds = 0.01f;
    public string LayerMaskName = "Default,TurtleBot3Manual";
    public string FrameId = "base_scan";

    float m_CurrentScanAngleStart;
    float m_CurrentScanAngleEnd;
    ROSConnection m_Ros;
    double m_TimeNextScanSeconds = -1;
    int m_NumMeasurementsTaken;
    List<float> ranges = new List<float>();
    LayerMask m_LayerMask;
    Collider[] m_SelfColliders;

    bool isScanning = false;
    double m_TimeLastScanBeganSeconds = -1;
    static double NowSec => Time.realtimeSinceStartupAsDouble;

    protected virtual void Start()
    {
        m_Ros = ROSConnection.GetOrCreateInstance();
        m_Ros.RegisterPublisher<LaserScanMsg>(topic);

        var layerNames = LayerMaskName
            .Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries);
        m_LayerMask = layerNames.Length > 0 ? LayerMask.GetMask(layerNames) : 0;
        if (m_LayerMask == 0)
        {
            Debug.LogWarning(
                $"LaserScanSensor[{name}] LayerMaskName '{LayerMaskName}' not found. " +
                "Falling back to all layers (self-filter will still apply)."
            );
            m_LayerMask = Physics.DefaultRaycastLayers;
        }

        // Exclude robot self-hits so Nav2 does not see the robot body as an obstacle.
        m_SelfColliders = GetComponentsInParent<Transform>()
            .SelectMany(t => t.GetComponents<Collider>())
            .Distinct()
            .ToArray();

        m_CurrentScanAngleStart = ScanAngleStartDegrees;
        m_CurrentScanAngleEnd = ScanAngleEndDegrees;

        m_TimeNextScanSeconds = NowSec + PublishPeriodSeconds;
    }

    void BeginScan()
    {
        isScanning = true;
        m_TimeLastScanBeganSeconds = NowSec;
        m_TimeNextScanSeconds = m_TimeLastScanBeganSeconds + PublishPeriodSeconds;
        m_NumMeasurementsTaken = 0;
    }

    public void EndScan()
    {
        if (ranges.Count == 0)
        {
            Debug.LogWarning($"Took {m_NumMeasurementsTaken} measurements but found no valid ranges");
        }
        else if (ranges.Count != m_NumMeasurementsTaken || ranges.Count != NumMeasurementsPerScan)
        {
            Debug.LogWarning($"Expected {NumMeasurementsPerScan} measurements. Actually took {m_NumMeasurementsTaken}" +
                             $"and recorded {ranges.Count} ranges.");
        }

        var now = NowSec;
        var sec = (int)now;
        var nsec = (uint)((now - Math.Floor(now)) * Clock.k_NanoSecondsInSeconds);
        // Invert the angle ranges when going from Unity to ROS
        var angleStartRos = -m_CurrentScanAngleStart * Mathf.Deg2Rad;
        var angleEndRos = -m_CurrentScanAngleEnd * Mathf.Deg2Rad;
        if (angleStartRos > angleEndRos)
        {
            Debug.LogWarning("LaserScan was performed in a clockwise direction but ROS expects a counter-clockwise scan, flipping the ranges...");
            var temp = angleEndRos;
            angleEndRos = angleStartRos;
            angleStartRos = temp;
            ranges.Reverse();
        }

        var msg = new LaserScanMsg
        {
            header = new HeaderMsg
            {
                frame_id = FrameId,
                stamp = new TimeMsg
                {
                    sec = sec,
                    nanosec = nsec,
                }
            },
            range_min = RangeMetersMin,
            range_max = RangeMetersMax,
            angle_min = angleStartRos,
            angle_max = angleEndRos,
            angle_increment = (angleEndRos - angleStartRos) / NumMeasurementsPerScan,
            time_increment = TimeBetweenMeasurementsSeconds,
            scan_time = (float)PublishPeriodSeconds,
            intensities = new float[ranges.Count],
            ranges = ranges.ToArray(),
        };
        
        m_Ros.Publish(topic, msg);

        m_NumMeasurementsTaken = 0;
        ranges.Clear();
        isScanning = false;
        if (now > m_TimeNextScanSeconds)
        {
            Debug.LogWarning($"Failed to complete scan started at {m_TimeLastScanBeganSeconds:F} before next scan was " +
                             $"scheduled to start: {m_TimeNextScanSeconds:F}, rescheduling to now ({now:F})");
            m_TimeNextScanSeconds = now;
        }

        m_CurrentScanAngleStart += ScanOffsetAfterPublish;
        m_CurrentScanAngleEnd += ScanOffsetAfterPublish;
        if (m_CurrentScanAngleStart > 360f || m_CurrentScanAngleEnd > 360f)
        {
            m_CurrentScanAngleStart -= 360f;
            m_CurrentScanAngleEnd -= 360f;
        }
    }

    public void Update()
    {
        if (!isScanning)
        {
            if (NowSec < m_TimeNextScanSeconds)
            {
                return;
            }

            BeginScan();
        }


        var measurementsSoFar = TimeBetweenMeasurementsSeconds == 0 ? NumMeasurementsPerScan :
            1 + Mathf.FloorToInt((float)(NowSec - m_TimeLastScanBeganSeconds) / TimeBetweenMeasurementsSeconds);
        if (measurementsSoFar > NumMeasurementsPerScan)
            measurementsSoFar = NumMeasurementsPerScan;

        var yawBaseDegrees = transform.rotation.eulerAngles.y;
        while (m_NumMeasurementsTaken < measurementsSoFar)
        {
            var t = m_NumMeasurementsTaken / (float)NumMeasurementsPerScan;
            var yawSensorDegrees = Mathf.Lerp(m_CurrentScanAngleStart, m_CurrentScanAngleEnd, t);
            var yawDegrees = yawBaseDegrees + yawSensorDegrees;
            var directionVector = Quaternion.Euler(0f, yawDegrees, 0f) * Vector3.forward;
            var measurementStart = RangeMetersMin * directionVector + transform.position;
            var measurementRay = new Ray(measurementStart, directionVector);

            var hits = Physics.RaycastAll(
                measurementRay,
                RangeMetersMax,
                m_LayerMask,
                QueryTriggerInteraction.Ignore
            );
            var foundValidMeasurement = false;
            var nearest = float.PositiveInfinity;
            foreach (var hit in hits)
            {
                if (hit.collider == null)
                    continue;
                if (System.Array.IndexOf(m_SelfColliders, hit.collider) >= 0)
                    continue;
                if (hit.distance < nearest)
                {
                    nearest = hit.distance;
                    foundValidMeasurement = true;
                }
            }

            // Only record measurement if it's within the sensor's operating range.
            ranges.Add(foundValidMeasurement ? nearest : float.PositiveInfinity);

            // Even if Raycast didn't find a valid hit, we still count it as a measurement
            ++m_NumMeasurementsTaken;
        }
        
        if (m_NumMeasurementsTaken >= NumMeasurementsPerScan)
        {
            if (m_NumMeasurementsTaken > NumMeasurementsPerScan)
            {
                Debug.LogError($"LaserScan has {m_NumMeasurementsTaken} measurements but we expected {NumMeasurementsPerScan}");
            }
            EndScan();
        }

    }
}
