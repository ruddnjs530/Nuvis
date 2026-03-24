using UnityEngine;
using Unity.Robotics.ROSTCPConnector;
using RosMessageTypes.Geometry;
using Unity.Robotics.UrdfImporter.Control;

namespace RosSharp.Control
{
    public enum ControlMode { Keyboard, ROS};

    public class AGVController : MonoBehaviour
    {
        public GameObject wheel1;
        public GameObject wheel2;
        public ControlMode mode = ControlMode.ROS;

        private ArticulationBody wA1;
        private ArticulationBody wA2;

        public float maxLinearSpeed = 2; //  m/s
        public float maxRotationalSpeed = 1;//
        public float wheelRadius = 0.033f; //meters
        public float trackWidth = 0.288f; // meters Distance between tyres
        public float forceLimit = 10;
        public float damping = 10;
        public bool invertLinearX = false;
        public bool invertAngularZ = true;
        public float minLinearCommand = 0.02f;
        public float minAngularCommand = 0.08f;
        public bool enableKinematicFallback = true;
        public float fallbackStuckSeconds = 0.4f;
        public float fallbackMinLinear = 0.03f;
        public float fallbackMinAngular = 0.10f;

        public float ROSTimeout = 0.5f;
        private float lastCmdReceived = 0f;

        ROSConnection ros;
        private RotationDirection direction;
        private float rosLinear = 0f;
        private float rosAngular = 0f;
        private Vector3 prevPosition;
        private Quaternion prevRotation;
        private float stuckTimer = 0f;

        void Start()
        {
            wA1 = wheel1.GetComponent<ArticulationBody>();
            wA2 = wheel2.GetComponent<ArticulationBody>();
            SetParameters(wA1);
            SetParameters(wA2);
            ros = ROSConnection.GetOrCreateInstance();
            ros.Subscribe<TwistMsg>("/cmd_vel", ReceiveROSCmd);
            prevPosition = transform.position;
            prevRotation = transform.rotation;
        }

        void ReceiveROSCmd(TwistMsg cmdVel)
        {
            rosLinear = (float)cmdVel.linear.x;
            rosAngular = (float)cmdVel.angular.z;
            lastCmdReceived = Time.realtimeSinceStartup;
        }

        void FixedUpdate()
        {
            if (mode == ControlMode.Keyboard)
            {
                KeyBoardUpdate();
            }
            else if (mode == ControlMode.ROS)
            {
                ROSUpdate();
            }     
        }

        private void SetParameters(ArticulationBody joint)
        {
            ArticulationDrive drive = joint.xDrive;
            drive.forceLimit = forceLimit;
            drive.damping = damping;
            joint.xDrive = drive;
        }

        private void SetSpeed(ArticulationBody joint, float wheelSpeed = float.NaN)
        {
            ArticulationDrive drive = joint.xDrive;
            if (float.IsNaN(wheelSpeed))
            {
                drive.targetVelocity = ((2 * maxLinearSpeed) / wheelRadius) * Mathf.Rad2Deg * (int)direction;
            }
            else
            {
                drive.targetVelocity = wheelSpeed;
            }
            joint.xDrive = drive;
        }

        private void KeyBoardUpdate()
        {
            float moveDirection = Input.GetAxis("Vertical");
            float inputSpeed;
            float inputRotationSpeed;
            if (moveDirection > 0)
            {
                inputSpeed = maxLinearSpeed;
            }
            else if (moveDirection < 0)
            {
                inputSpeed = maxLinearSpeed * -1;
            }
            else
            {
                inputSpeed = 0;
            }

            float turnDirction = Input.GetAxis("Horizontal");
            if (turnDirction > 0)
            {
                inputRotationSpeed = maxRotationalSpeed;
            }
            else if (turnDirction < 0)
            {
                inputRotationSpeed = maxRotationalSpeed * -1;
            }
            else
            {
                inputRotationSpeed = 0;
            }
            RobotInput(inputSpeed, inputRotationSpeed);
        }


        private void ROSUpdate()
        {
            if (Time.realtimeSinceStartup - lastCmdReceived > ROSTimeout)
            {
                rosLinear = 0f;
                rosAngular = 0f;
            }
            float linear = invertLinearX ? -rosLinear : rosLinear;
            float angular = invertAngularZ ? -rosAngular : rosAngular;

            // Help articulation dynamics overcome tiny command deadbands.
            if (Mathf.Abs(linear) > 0f && Mathf.Abs(linear) < minLinearCommand)
            {
                linear = Mathf.Sign(linear) * minLinearCommand;
            }
            if (Mathf.Abs(angular) > 0f && Mathf.Abs(angular) < minAngularCommand)
            {
                angular = Mathf.Sign(angular) * minAngularCommand;
            }

            RobotInput(linear, angular);
            TryKinematicFallback(linear, angular);
        }

        private void RobotInput(float speed, float rotSpeed) // m/s and rad/s
        {
            speed = Mathf.Clamp(speed, -maxLinearSpeed, maxLinearSpeed);
            rotSpeed = Mathf.Clamp(rotSpeed, -maxRotationalSpeed, maxRotationalSpeed);
            float wheel1Rotation = (speed / wheelRadius);
            float wheel2Rotation = wheel1Rotation;
            float wheelSpeedDiff = ((rotSpeed * trackWidth) / wheelRadius);
            if (rotSpeed != 0)
            {
                wheel1Rotation = (wheel1Rotation + (wheelSpeedDiff / 1)) * Mathf.Rad2Deg;
                wheel2Rotation = (wheel2Rotation - (wheelSpeedDiff / 1)) * Mathf.Rad2Deg;
            }
            else
            {
                wheel1Rotation *= Mathf.Rad2Deg;
                wheel2Rotation *= Mathf.Rad2Deg;
            }
            SetSpeed(wA1, wheel1Rotation);
            SetSpeed(wA2, wheel2Rotation);
        }

        private void TryKinematicFallback(float linear, float angular)
        {
            if (!enableKinematicFallback)
            {
                prevPosition = transform.position;
                prevRotation = transform.rotation;
                stuckTimer = 0f;
                return;
            }

            var cmdActive = Mathf.Abs(linear) > 0.001f || Mathf.Abs(angular) > 0.001f;
            if (!cmdActive)
            {
                prevPosition = transform.position;
                prevRotation = transform.rotation;
                stuckTimer = 0f;
                return;
            }

            var moved = Vector3.Distance(transform.position, prevPosition);
            var turned = Quaternion.Angle(transform.rotation, prevRotation);
            if (moved < 0.0005f && turned < 0.05f)
            {
                stuckTimer += Time.fixedDeltaTime;
            }
            else
            {
                stuckTimer = 0f;
            }

            prevPosition = transform.position;
            prevRotation = transform.rotation;

            if (stuckTimer < fallbackStuckSeconds)
            {
                return;
            }

            var kLinear = Mathf.Abs(linear) < fallbackMinLinear
                ? Mathf.Sign(linear) * fallbackMinLinear
                : linear;
            var kAngular = Mathf.Abs(angular) < fallbackMinAngular
                ? Mathf.Sign(angular) * fallbackMinAngular
                : angular;
            if (Mathf.Abs(linear) <= 0.001f)
            {
                kLinear = 0f;
            }
            if (Mathf.Abs(angular) <= 0.001f)
            {
                kAngular = 0f;
            }

            transform.position += transform.forward * (kLinear * Time.fixedDeltaTime);
            transform.Rotate(0f, kAngular * Mathf.Rad2Deg * Time.fixedDeltaTime, 0f, Space.World);
        }
    }
}
