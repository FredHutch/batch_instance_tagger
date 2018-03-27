#!/usr/bin/env python3
"""
A lambda function that tags EC2 instances started by AWS Batch as they are supposed
to be tagged, but are (sometimes at least) not, possibly due to a bug in Batch.
"""

import logging

import boto3

def lambda_handler(event, context): # pylint: disable=unused-argument, too-many-return-statements
    "here it is"
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ec2_client = boto3.client("ec2")
    logger.info("we got us an event, Hoo boy.\n%s", event)
    if not event['detail']['eventName'] == 'CreateTags': # should never happen
        logger.info("This is not a CreateTags event")
        return
    # if not event["detail"]["userIdentity"]["type"] == "Root":
    #     logger.info("User identity type is not Root, exiting")
    #     return
    if not 'invokedBy' in event['detail']['userIdentity']:
        logger.info("invokedBy key not found in event['detail']['userIdentity'], not tagging")
        return
    if not event['detail']['userIdentity']['invokedBy'] == "autoscaling.amazonaws.com":
        logger.info("This event not invoked by autoscaling")
        return
    if not len(event["detail"]["requestParameters"]["tagSet"]["items"]) == 1:
        logger.info("More than one tagSet pair present, not tagging")
        return
    existing_tag = event["detail"]["requestParameters"]["tagSet"]["items"][0]
    if not existing_tag["key"] == "aws:autoscaling:groupName":
        logger.info("Tag key is not 'aws:autoscaling:groupName' but %s",
                    existing_tag["key"])
        return
    asg_name = existing_tag['value']

    # instance_id = event["detail"]["requestParameters"]["resourcesSet"]["items"][0]["resourceId"]
    instance_ids = []
    for item in event["detail"]["requestParameters"]["resourcesSet"]["items"]:
        if item['resourceId'].startswith("i-"):
            instance_ids.append(item["resourceId"])
    if not instance_ids:
        logger.info("No resource id was an instance ID, exiting.")
        return

    batch_client = boto3.client("batch")
    envs = batch_client.describe_compute_environments()['computeEnvironments']
    for env in envs:
        if asg_name.startswith(env['computeEnvironmentName']):
            env_tags = env['computeResources']['tags']
            env_tags['TAGGED_BY_LAMBDA_FUNCTION'] = 'yes'
            env_tags["aws_autoscaling_groupName"] = asg_name
            ec2_tags = []
            for key in env_tags.keys():
                ec2_tags.append(dict(Key=key, Value=env_tags[key]))
            logger.info("Tagging instances %s with tags:\n%s", ",".join(instance_ids), ec2_tags)
            ec2_client.create_tags(Resources=instance_ids, Tags=ec2_tags)
            return
    logger.info("Found no compute environment with which to tag instances %s", instance_ids)
