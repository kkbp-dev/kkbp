using System;
using System.Text;

namespace KKBP.Exporter.Core
{
    // The closed sets from contract/schema/sets/. Each member's contract name is its
    // C# name in snake_case; a test checks these enums against the schema files.

    /// <summary>Unity's HumanBodyBones, then the KKBP extras.</summary>
    public enum BoneRole
    {
        Hips, LeftUpperLeg, RightUpperLeg, LeftLowerLeg, RightLowerLeg, LeftFoot, RightFoot,
        Spine, Chest, Neck, Head, LeftShoulder, RightShoulder, LeftUpperArm, RightUpperArm,
        LeftLowerArm, RightLowerArm, LeftHand, RightHand, LeftToes, RightToes, LeftEye, RightEye, Jaw,
        LeftThumbProximal, LeftThumbIntermediate, LeftThumbDistal,
        LeftIndexProximal, LeftIndexIntermediate, LeftIndexDistal,
        LeftMiddleProximal, LeftMiddleIntermediate, LeftMiddleDistal,
        LeftRingProximal, LeftRingIntermediate, LeftRingDistal,
        LeftLittleProximal, LeftLittleIntermediate, LeftLittleDistal,
        RightThumbProximal, RightThumbIntermediate, RightThumbDistal,
        RightIndexProximal, RightIndexIntermediate, RightIndexDistal,
        RightMiddleProximal, RightMiddleIntermediate, RightMiddleDistal,
        RightRingProximal, RightRingIntermediate, RightRingDistal,
        RightLittleProximal, RightLittleIntermediate, RightLittleDistal,
        UpperChest,
        BodyRoot, FaceRoot, LeftBreast, RightBreast, TongueRoot,
        LeftHandIk, RightHandIk, LeftFootIk, RightFootIk,
        LeftElbowPole, RightElbowPole, LeftKneePole, RightKneePole,
    }

    public enum BoneGroup
    {
        Deform, Helper, Skirt, Breast, Hair, Accessory, Face, Eye, Eyebrow, Mouth, Nsfw,
    }

    public enum MaterialRole
    {
        Body, Face, Eyebrow, Eyelash, Eyelid, EyelineUpper, EyelineLower, EyelineShadow, NoseLine,
        EyeWhite, EyeL, EyeR, GagEyes, Tongue, Teeth, Tears, Hair,
    }

    public enum BlendMode
    {
        Opaque, Cutout, Alpha, Glasses,
    }

    public enum TextureRole
    {
        Main, ColorMask, Normal, DetailNormal, AlphaMask, LineMask, DetailMask, Overlay,
    }

    public enum TextureVariant
    {
        Light, Dark, LightNoEyeshadow, DarkNoEyeshadow,
    }

    public enum ExpressionCategory
    {
        Eye, Mouth, Eyebrow, Gag, Tears, Other,
    }

    public static class ContractNames
    {
        /// <summary>The contract's name for a closed-set member, such as <c>left_upper_arm</c>.</summary>
        public static string Of(Enum value)
        {
            return SnakeCase(Enum.GetName(value.GetType(), value));
        }

        public static string[] All(Type enumType)
        {
            var values = Enum.GetValues(enumType);
            var result = new string[values.Length];
            for (int i = 0; i < values.Length; i++)
            {
                result[i] = Of((Enum)values.GetValue(i));
            }
            return result;
        }

        /// <summary>True for Material Roles that may appear at most once per bundle (the set's x-unique list).</summary>
        public static bool IsUnique(MaterialRole role)
        {
            switch (role)
            {
                case MaterialRole.EyeWhite:
                case MaterialRole.GagEyes:
                case MaterialRole.Tongue:
                case MaterialRole.Teeth:
                case MaterialRole.Tears:
                case MaterialRole.Hair:
                    return false;
                default:
                    return true;
            }
        }

        /// <summary>True for Texture Roles that are unique within a material for each Variant and pattern.</summary>
        public static bool IsUnique(TextureRole role)
        {
            return role != TextureRole.Overlay;
        }

        internal static string SnakeCase(string name)
        {
            var sb = new StringBuilder();
            for (int i = 0; i < name.Length; i++)
            {
                char c = name[i];
                if (char.IsUpper(c))
                {
                    if (i > 0)
                    {
                        sb.Append('_');
                    }
                    sb.Append(char.ToLowerInvariant(c));
                }
                else
                {
                    sb.Append(c);
                }
            }
            return sb.ToString();
        }

        /// <summary>The category an Expression Name's prefix implies, or null if it has no known prefix.</summary>
        public static ExpressionCategory? CategoryOf(string expressionName)
        {
            int space = expressionName.IndexOf(' ');
            string prefix = space < 0 ? expressionName : expressionName.Substring(0, space);
            switch (prefix)
            {
                case "Eye": return ExpressionCategory.Eye;
                case "Mouth": return ExpressionCategory.Mouth;
                case "Eyebrow": return ExpressionCategory.Eyebrow;
                case "Gag": return ExpressionCategory.Gag;
                case "Tears": return ExpressionCategory.Tears;
                default: return null;
            }
        }
    }

    /// <summary>A problem with the captured data that stops the export.</summary>
    public class ExportException : Exception
    {
        public ExportException(string message) : base(message)
        {
        }

        public ExportException(string message, Exception inner) : base(message, inner)
        {
        }
    }
}
